#!/usr/bin/env python3
"""Decide whether a build is needed: has Arch Linux's extra/telegram-desktop
got a version (pkgver-pkgrel) this repository has no release for yet?

Prints GitHub step outputs: pkgver, pkgrel, build.
"""
import argparse
import json
import os
import subprocess
import urllib.request

ARCH_JSON = "https://archlinux.org/packages/extra/x86_64/telegram-desktop/json/"


def release_exists(repo, tag):
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/releases/tags/{tag}"],
        capture_output=True, text=True)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", default="false")
    args = parser.parse_args()

    with urllib.request.urlopen(ARCH_JSON, timeout=30) as response:
        info = json.load(response)
    pkgver, pkgrel = info["pkgver"], info["pkgrel"]
    tag = f"pkg-{pkgver}-{pkgrel}"
    force = args.force.lower() == "true"
    build = force or not release_exists(os.environ["REPO"], tag)
    print(f"pkgver={pkgver}")
    print(f"pkgrel={pkgrel}")
    print(f"build={'true' if build else 'false'}")


if __name__ == "__main__":
    main()
