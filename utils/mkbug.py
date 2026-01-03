#!/usr/bin/env python3
import argparse
import datetime
import json
import re
import shutil
import subprocess
from pathlib import Path

import requests

BUGS_FILE = "docs/BUGS.md"
CONFIG_FILE = Path.home() / ".mkbug_config.json"

# Anchor blocks (no spaces after colon, per your file)
SUMMARY_BLOCK = re.compile(
    r"(?s)<!--\s*BUGS:SUMMARY START\s*-->(.*?)<!--\s*BUGS:SUMMARY END\s*-->"
)
DETAILS_BLOCK = re.compile(
    r"(?s)<!--\s*BUGS:DETAILS START\s*-->(.*?)<!--\s*BUGS:DETAILS END\s*-->"
)

# Your summary table header (kept stable so we can regenerate rows safely)
SUMMARY_HEADER = ("\n| ID        | Title                   | Severity | Status        | Opened      | Owner | Target |\n"
"|-----------|-------------------------|----------|---------------|-------------|-------|--------|\n")

DETAIL_TEMPLATE = """### BUG-{id} — {title}

- **Severity:** {severity} · **Status:** {status} · **Affects:** {area}
- **Repro:** {steps}
- **Expected/Actual:** {expected} / {actual}
- **Notes:** {notes}
- **Owner:** {owner}
- **Target:** {target}

"""


def ensure_scaffold(text: str) -> str:
    """Ensure BUGS.md has required sections + anchors. If not, create a sane base."""
    if not text.strip():
        base = (
            "# BUGS\n\n"
            "_Source of truth for **open** bugs. Resolved items live in **CHANGELOG.md** (v0.1.0)._\n\n"
            "## Legend\n\n"
            "- **Severity:** P0 (blocker) · P1 (major) · P2 (minor) · P3 (nit)\n"
            "- **Status:** Open · Triaged · In Progress · Blocked · Needs Verify\n\n"
            "---\n\n"
            "## Open Bugs (summary)\n"
            "<!-- BUGS:SUMMARY START -->\n"
            + SUMMARY_HEADER
            + "<!-- BUGS:SUMMARY END -->\n"
            "---\n\n"
            "## Details\n"
            "<!-- BUGS:DETAILS START -->\n"
            "<!-- BUGS:DETAILS END -->\n"
            "---\n\n"
            "## Recently Resolved → see CHANGELOG.md (v0.1.0)\n"
        )
        return base

    if not SUMMARY_BLOCK.search(text):
        # Insert empty summary block after the "## Open Bugs (summary)" heading
        text = re.sub(
            r"(?m)^## Open Bugs \(summary\)\s*$",
            "## Open Bugs (summary)\n<!-- BUGS:SUMMARY START -->\n"
            + SUMMARY_HEADER
            + "<!-- BUGS:SUMMARY END -->",
            text,
        )
    if not DETAILS_BLOCK.search(text):
        # Insert empty details block after the "## Details" heading
        text = re.sub(
            r"(?m)^## Details\s*$",
            "## Details\n<!-- BUGS:DETAILS START -->\n<!-- BUGS:DETAILS END -->",
            text,
        )
    return text


def replace_between(pattern: re.Pattern, text: str, new_inner: str) -> str:
    m = pattern.search(text)
    if not m:
        raise RuntimeError("BUGS.md anchors not found; run once to scaffold.")
    return text[: m.start(1)] + new_inner + text[m.end(1) :]


def map_severity_to_p(sev: str) -> str:
    sev = sev.strip().lower()
    table = {"critical": "P0", "high": "P1", "medium": "P2", "low": "P3"}
    # If they already typed P0/P1/..., pass through
    if re.fullmatch(r"p[0-3]", sev):
        return sev.upper()
    return table.get(sev, "P2")


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {}


def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def upsert_summary(md: str, bug: dict) -> str:
    # Extract current rows
    m = SUMMARY_BLOCK.search(md)
    inner = m.group(1) if m else ""
    # Keep the header constant; extract existing data rows (lines that start with | BUG-)
    lines = [L for L in inner.splitlines() if L.strip()]
    # Drop any existing header lines; keep only rows
    rows = [L for L in lines if L.startswith("| BUG-")]

    # Build/replace this bug's row (truncate overly long titles to keep table tidy)
    title = bug["title"]
    if len(title) > 23:  # keep width similar to your table
        title = title[:23]

    row = f"| BUG-{bug['id']:04d}  | {title:<23} | {bug['severity']:<8} | {bug['status']:<13} | {bug['opened']}  | {bug['owner'] or '':<5} | {bug['target']} |"

    replaced = False
    for i, r in enumerate(rows):
        if re.search(rf"\|\s*BUG-{bug['id']:04d}\s*\|", r):
            rows[i] = row
            replaced = True
            break
    if not replaced and bug["status"] != "Resolved":
        rows.append(row)
    if bug["status"] == "Resolved":
        rows = [r for r in rows if not re.search(rf"\|\s*BUG-{bug['id']:04d}\s*\|", r)]

    # Sort by BUG number ascending
    def bugnum(r):
        m = re.search(r"BUG-(\d{4})", r)
        return int(m.group(1)) if m else 99999

    rows = sorted(rows, key=bugnum)

    new_inner = SUMMARY_HEADER + "\n".join(rows) + ("\n" if rows else "")
    return replace_between(SUMMARY_BLOCK, md, new_inner)


def upsert_details(md: str, bug: dict) -> str:
    m = DETAILS_BLOCK.search(md)
    if not m:
        raise RuntimeError("BUGS.md details anchors not found.")
    details = m.group(1)

    # One section per bug, up to next "### BUG-#### —" or end
    pat = re.compile(
        rf"(?ms)^### BUG-{bug['id']:04d}\s+—\s+.*?$.*?(?=^### BUG-\d{{4}}\s+—|\Z)"
    )

    block = DETAIL_TEMPLATE.format(
        id=bug["id"],
        title=bug["title"],
        severity=bug["severity"],
        status=bug["status"],
        area=bug["area"],
        steps=bug["steps"] or "-",
        expected=bug["expected"] or "-",
        actual=bug["actual"] or "-",
        notes=bug["notes"] or "-",
        owner=bug["owner"],
        target=bug["target"],
    )

    match = pat.search(details)
    if match:
        # Replace only heading+meta, keep any user content after the meta block
        section = match.group(0)
        parts = re.split(r"\n{2,}", section, maxsplit=2)
        new_section = block.rstrip() + ("\n\n" + parts[2] if len(parts) == 3 else "\n")
        details = details[: match.start()] + new_section + details[match.end() :]
    else:
        details = details.rstrip() + ("\n\n" if details.strip() else "") + block

    return md[: m.start(1)] + details + md[m.end(1) :]


def main():
    ap = argparse.ArgumentParser(
        description="Log a bug and (optionally) create a GH issue/branch."
    )
    ap.add_argument(
        "--no-branch", action="store_true", help="Do not create a git branch."
    )
    ap.add_argument(
        "--no-issue", action="store_true", help="Do not create a GitHub issue."
    )
    ap.add_argument("--file", default=BUGS_FILE)
    args = ap.parse_args()

    cfg = load_config()
    if not {"github_owner", "github_repo", "github_token"} <= cfg.keys():
        print("[*] First-time setup:")
        cfg["github_owner"] = input("GitHub owner/org: ").strip()
        cfg["github_repo"] = input("GitHub repo name: ").strip()
        cfg["github_token"] = input(
            "GitHub personal access token (repo scope): "
        ).strip()
        save_config(cfg)
        print(f"[+] Saved config to {CONFIG_FILE}")

    cfg.setdefault("next_bug_id", 1001)
    bug_num = cfg["next_bug_id"]
    cfg["next_bug_id"] = bug_num + 1
    save_config(cfg)

    today = datetime.date.today().isoformat()

    # Collect info (tweaked prompts to match new format)
    title = input("Bug Title: ").strip()
    if not title:
        print("Bug title is required.")
        return
    area = input("Area (calendar|jobs|auth|admin|css|misc): ").strip() or "misc"
    sev_raw = (
        input("Severity (P0|P1|P2|P3 or Critical|High|Medium|Low) [P2]: ").strip()
        or "P2"
    )
    severity = map_severity_to_p(sev_raw)
    steps = input("Repro steps (one-liner OK): ").strip()
    expected = input("Expected behavior: ").strip()
    actual = input("Actual behavior: ").strip()
    owner = input("Owner (@handle) [blank ok]: ").strip()
    target = input("Target (e.g., v0.1.1) [v0.1.1]: ").strip() or "v0.1.1"

    # IDs and branch
    bug_id = bug_num
    short_slug = slugify(title)[:20]
    branch_name = f"fix/bug-{bug_num:04d}-{short_slug}"

    # Read/prepare BUGS.md
    p = Path(args.file)
    md = p.read_text(encoding="utf-8") if p.exists() else ""
    md = ensure_scaffold(md)

    bug = dict(
        id=bug_id,
        title=title,
        severity=severity,
        status="Open",
        opened=today,
        owner=owner,
        target=target,
        area=area,
        steps=steps,
        expected=expected,
        actual=actual,
        notes="-",
    )

    # Update summary + details
    md = upsert_summary(md, bug)
    md = upsert_details(md, bug)
    # Backup then write
    shutil.copyfile(p, p.with_suffix(p.suffix + ".bak")) if p.exists() else None
    p.write_text(md, encoding="utf-8")
    print(f"[+] Updated {p}")

    # Create GitHub issue (optional)
    issue_number = None
    if not args.no_issue:
        if shutil.which("gh"):
            body = DETAIL_TEMPLATE.format(
                id=bug_id,
                title=title,
                severity=severity,
                status="Open",
                area=area,
                steps=steps or "-",
                expected=expected or "-",
                actual=actual or "-",
                notes="-",
                owner=owner,
                target=target,
            ).strip()
            cmd = [
                "gh",
                "issue",
                "create",
                "--repo",
                f"{cfg['github_owner']}/{cfg['github_repo']}",
                "--title",
                f"{title} (BUG-{bug_id:04d})",
                "--body",
                body,
                "--label",
                "bug",
                "--label",
                severity.lower(),
                "--label",
                area.lower(),
                "--json",
                "number",
                "--jq",
                ".number",
            ]
            cp = subprocess.run(cmd, capture_output=True, text=True)
            if cp.returncode == 0 and cp.stdout.strip().isdigit():
                issue_number = int(cp.stdout.strip())
                print(f"[+] Created GitHub issue #{issue_number} via gh")
            else:
                print(f"[!] gh issue create failed:\n{cp.stderr}")
        else:
            url = f"https://api.github.com/repos/{cfg['github_owner']}/{cfg['github_repo']}/issues"
            headers = {
                "Authorization": f"Bearer {cfg['github_token']}",
                "Accept": "application/vnd.github.v3+json",
            }
            body = DETAIL_TEMPLATE.format(
                id=bug_id,
                title=title,
                severity=severity,
                status="Open",
                area=area,
                steps=steps or "-",
                expected=expected or "-",
                actual=actual or "-",
                notes="-",
                owner=owner,
                target=target,
            ).strip()
            payload = {
                "title": f"{title} (BUG-{bug_id:04d})",
                "body": body,
                "labels": ["bug", severity.lower(), area.lower()],
            }
            r = requests.post(url, headers=headers, json=payload)
            if r.status_code == 201:
                issue_number = r.json()["number"]
                print(f"[+] Created GitHub issue #{issue_number}")
            else:
                print(f"[!] Failed to create GitHub issue: {r.status_code} {r.text}")

    # Commit BUGS.md change to dev
    subprocess.run(["git", "checkout", "dev"], check=True)
    subprocess.run(["git", "pull", "--ff-only"], check=True)
    subprocess.run(["git", "add", str(p)], check=True)

    commit_msg = f"chore(buglog): add BUG-{bug_id:04d}\n\nReferences: BUG-{bug_id:04d}"
    if issue_number:
        commit_msg += f"\nRefs #{issue_number}"
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "push", "origin", "dev"], check=True)

    # Create branch unless suppressed
    if not args.no_branch:
        subprocess.run(["git", "branch", branch_name, "dev"], check=True)
        print(f"[+] Created branch {branch_name} from dev (staying on dev)")
    else:
        print("[i] Skipped branch creation (--no-branch).")


if __name__ == "__main__":
    main()
