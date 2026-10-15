#!/usr/bin/env python3
"""Make the telegram-desktop-export PKGBUILD from Arch Linux's
extra/telegram-desktop PKGBUILD of the same version.

Arch's maintainers already keep the build working for each release (the
TDLib commit, wallet-engine, dependencies, flags), so their PKGBUILD is
taken as is and only changed to: a new name, provides/conflicts, no LTO,
and the export patch applied in prepare().

Output: work/out/telegram-desktop-export/ with PKGBUILD, the patch, any
local files of Arch's package, and aur-files (what goes to the AUR).
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys

ARCH_GIT = ("https://gitlab.archlinux.org/archlinux/packaging/packages/"
            "telegram-desktop.git")
NAME = "telegram-desktop-export"
PATCH = "export-patches.patch"
REPO_URL = "https://github.com/{repo}"
DESCRIPTION = ("Telegram Desktop with export patches: media reused between "
               "exports, size limits per media type, no hangs on lost media")


def fail(message):
    print(f"make_pkgbuilds: {message}", file=sys.stderr)
    with open("work/failure.md", "w") as f:
        f.write(f"Couldn't adapt Arch's PKGBUILD: {message}\n")
    sys.exit(1)


def array_span(text, name):
    """Start and end (after ')') of a bash array assignment name=(...)."""
    m = re.search(rf"^{name}=\(", text, re.M)
    if not m:
        return None
    depth, i = 0, m.end() - 1
    while i < len(text):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return m.start(), i + 1
        elif text[i] == "#":
            i = text.index("\n", i)
            continue
        i += 1
    fail(f"unterminated {name}=(")


def append_to_array(text, name, item):
    """Add an item after the last one, aligned like it."""
    span = array_span(text, name)
    if not span:
        fail(f"no {name}=( in the PKGBUILD")
    close = span[1] - 1
    before = text[:close].rstrip()
    last = before.splitlines()[-1]
    if last.startswith(f"{name}=("):
        indent = " " * len(f"{name}=(")
    else:
        indent = re.match(r"\s*", last).group()
    closing_on_own_line = "\n" in text[len(before):close]
    tail = "\n" if closing_on_own_line else ""
    return f"{before}\n{indent}{item}{tail}{text[close:]}"


def main():
    pkgver, pkgrel = os.environ["PKGVER"], os.environ["PKGREL"]
    repo_url = REPO_URL.format(repo=os.environ["REPO"])
    out = os.path.join("work", "out", NAME)
    arch = os.path.join("work", "arch")
    shutil.rmtree(arch, ignore_errors=True)
    subprocess.run(["git", "-c", "advice.detachedHead=false", "clone",
                    "--quiet", "--depth", "1", "--branch",
                    f"{pkgver}-{pkgrel}", ARCH_GIT, arch], check=True)
    with open(os.path.join(arch, "PKGBUILD")) as f:
        text = f.read()

    # Credits: Arch's maintainers stay as contributors.
    header, body = re.match(r"((?:#[^\n]*\n)*)(.*)", text, re.S).groups()
    credits = [re.sub(r"^# Maintainer:", "# Contributor:", line)
               for line in header.splitlines() if line.startswith("# ")]
    header = "\n".join([
        "# Maintainer: Remenod <remenod@gmail.com>",
        *credits,
        f"# Generated from Arch Linux's extra/telegram-desktop {pkgver}-{pkgrel}",
        f"# by {repo_url} (packaging branch).",
    ]) + "\n\n"
    text = header + body.lstrip("\n")

    if not re.search(r"^pkgname=telegram-desktop$", text, re.M):
        fail("pkgname isn't telegram-desktop")
    text = re.sub(r"^pkgname=.*$", f"pkgname={NAME}", text, count=1,
                  flags=re.M)
    text = re.sub(r"^pkgdesc=.*$", f"pkgdesc='{DESCRIPTION}'", text,
                  count=1, flags=re.M)
    text = re.sub(r"^url=.*$", f'url="{repo_url}"', text, count=1,
                  flags=re.M)
    if re.search(r"^(provides|conflicts|options)=", text, re.M):
        fail("Arch's PKGBUILD has provides/conflicts/options now")
    license_line = re.search(r"^license=.*$", text, re.M)
    if not license_line:
        fail("no license= line")
    text = (text[:license_line.end()]
            + "\nprovides=('telegram-desktop')"
            + "\nconflicts=('telegram-desktop')"
            + "\n# LTO makes the build several times slower and hungrier."
            + "\noptions=('!lto' '!debug')"
            + text[license_line.end():])

    # The patch goes last in source=() with its checksum in every sums=().
    with open(os.path.join("work", PATCH), "rb") as f:
        patch = f.read()
    text = append_to_array(text, "source", PATCH)
    sums = 0
    for algo in ("sha512", "sha256", "b2"):
        if array_span(text, f"{algo}sums"):
            digest = (hashlib.blake2b(patch).hexdigest() if algo == "b2"
                      else hashlib.new(algo, patch).hexdigest())
            text = append_to_array(text, f"{algo}sums", f"'{digest}'")
            sums += 1
    if not sums:
        fail("no checksums array")

    # The tdesktop sources come as tdesktop-$pkgver-full.tar.gz.
    if "tdesktop-${pkgver}-full.tar.gz" not in text:
        fail("the tdesktop tarball isn't tdesktop-${pkgver}-full.tar.gz")
    apply = ('  patch -Np1 -d "$srcdir/tdesktop-$pkgver-full" '
             f'-i "$srcdir/{PATCH}"\n')
    prepare = re.search(r"^prepare\(\) \{\n", text, re.M)
    if prepare:
        text = text[:prepare.end()] + apply + text[prepare.end():]
    else:
        build = re.search(r"^build\(\) \{", text, re.M)
        if not build:
            fail("no build()")
        text = (text[:build.start()] + "prepare() {\n" + apply + "}\n\n"
                + text[build.start():])

    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    with open(os.path.join(out, "PKGBUILD"), "w") as f:
        f.write(text)
    shutil.copy(os.path.join("work", PATCH), out)
    # Local files of Arch's package (patches etc.) go along.
    files = ["PKGBUILD", ".SRCINFO", PATCH]
    for name in sorted(os.listdir(arch)):
        path = os.path.join(arch, name)
        if (os.path.isfile(path) and name not in ("PKGBUILD", ".SRCINFO",
                                                  ".nvchecker.toml")
                and not name.startswith(".") and name != "REUSE.toml"
                and not name.startswith("LICENSE")):
            shutil.copy(path, out)
            files.append(name)
    with open(os.path.join(out, "aur-files"), "w") as f:
        f.write("\n".join(files) + "\n")
    subprocess.run(["bash", "-n", os.path.join(out, "PKGBUILD")], check=True)
    print(f"{out}/PKGBUILD ready, AUR files: {', '.join(files)}")


if __name__ == "__main__":
    main()
