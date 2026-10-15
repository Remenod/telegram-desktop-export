#!/usr/bin/env python3
"""Decide whether a build is needed: has Arch Linux's extra/telegram-desktop
got a version (pkgver-pkgrel) this repository has no release for yet?

A version whose build failed (an open "Build failed: <version>" issue) is
not retried every hour: that would only repeat the failure and the mail.
It is built again by a manual run with force, or when Arch moves on.

With --republish the existing release is published to the AUR again
without building (mode=republish).

Prints GitHub step outputs: pkgver, pkgrel, build, mode.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

ARCH_JSON = "https://archlinux.org/packages/extra/x86_64/telegram-desktop/json/"


def release_exists(repo, tag):
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/releases/tags/{tag}"],
        capture_output=True, text=True)
    return result.returncode == 0


def failure_open(repo, version):
    title = f"Build failed: {version}"
    found = json.loads(subprocess.run(
        ["gh", "issue", "list", "--repo", repo, "--state", "open",
         "--search", f'"{title}" in:title', "--json", "title"],
        check=True, capture_output=True, text=True).stdout)
    return any(issue["title"] == title for issue in found)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", default="false")
    parser.add_argument("--republish", default="false")
    args = parser.parse_args()

    with urllib.request.urlopen(ARCH_JSON, timeout=30) as response:
        info = json.load(response)
    pkgver, pkgrel = info["pkgver"], info["pkgrel"]
    repo = os.environ["REPO"]
    tag = f"pkg-{pkgver}-{pkgrel}"
    force = args.force.lower() == "true"
    mode = "build"
    if args.republish.lower() == "true":
        if not release_exists(repo, tag):
            sys.exit(f"no release {tag} to publish again")
        build, mode = True, "republish"
    elif force:
        build = True
    elif release_exists(repo, tag):
        build = False
    elif failure_open(repo, f"{pkgver}-{pkgrel}"):
        print(f"skipping {pkgver}-{pkgrel}: its build failed, see the issue",
              file=sys.stderr)
        build = False
    else:
        build = True
    print(f"pkgver={pkgver}")
    print(f"pkgrel={pkgrel}")
    print(f"build={'true' if build else 'false'}")
    print(f"mode={mode}")


if __name__ == "__main__":
    main()
