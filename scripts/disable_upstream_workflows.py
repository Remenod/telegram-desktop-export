#!/usr/bin/env python3
"""Disable every workflow of this fork except packaging.yml.

Patch branches are based on Telegram Desktop release tags, which carry
upstream's own workflows (Windows, macOS, snap builds...); those must not
run here. New upstream workflows get disabled on the next check.
"""
import json
import os
import subprocess

KEEP = {".github/workflows/packaging.yml"}


def gh(*args):
    return subprocess.run(["gh", "api", *args], check=True,
                          capture_output=True, text=True).stdout


def main():
    repo = f"repos/{os.environ['REPO']}"
    workflows = json.loads(gh(f"{repo}/actions/workflows?per_page=100"))
    for workflow in workflows["workflows"]:
        if workflow["path"] in KEEP or workflow["state"] != "active":
            continue
        gh("-X", "PUT", f"{repo}/actions/workflows/{workflow['id']}/disable")
        print("disabled", workflow["path"])


if __name__ == "__main__":
    main()
