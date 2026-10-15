#!/usr/bin/env python3
"""Open an issue for a failed build (or comment on the open one of the same
version), with what went wrong when a step left work/failure.md."""
import json
import os
import subprocess


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True,
                          text=True).stdout


def main():
    repo = os.environ["REPO"]
    version = f"{os.environ.get('PKGVER') or '?'}-{os.environ.get('PKGREL') or '?'}"
    title = f"Build failed: {version}"
    details = ""
    if os.path.exists("work/failure.md"):
        with open("work/failure.md") as f:
            details = f.read().strip() + "\n\n"
    body = (f"{details}Run: {os.environ['RUN_URL']}\n\n"
            "Until this is fixed the AUR packages stay at the previous "
            "version.")
    found = json.loads(gh("issue", "list", "--repo", repo, "--state", "open",
                          "--search", f'"{title}" in:title',
                          "--json", "number,title"))
    same = [i for i in found if i["title"] == title]
    if same:
        gh("issue", "comment", str(same[0]["number"]), "--repo", repo,
           "--body", body)
        print("commented on issue", same[0]["number"])
    else:
        print(gh("issue", "create", "--repo", repo, "--title", title,
                 "--body", body).strip())


if __name__ == "__main__":
    main()
