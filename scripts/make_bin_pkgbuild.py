#!/usr/bin/env python3
"""Write the telegram-desktop-export-bin PKGBUILD for the package built in
OUT/telegram-desktop-export: it downloads that package from this
repository's GitHub release and unpacks it, with the dependencies taken
from the package's own .PKGINFO."""
import glob
import hashlib
import os
import subprocess
import sys

NAME = "telegram-desktop-export"


def quote(value):
    return "'" + value.replace("'", "'\\''") + "'"


def array(name, values):
    if not values:
        return ""
    items = "\n".join(f"  {quote(v)}" for v in values)
    return f"{name}=(\n{items}\n)\n"


def main():
    out = sys.argv[1]
    pkgver, pkgrel = os.environ["PKGVER"], os.environ["PKGREL"]
    repo = os.environ["REPO"]
    files = glob.glob(os.path.join(
        out, NAME, f"{NAME}-{pkgver}-{pkgrel}-x86_64.pkg.tar.zst"))
    if len(files) != 1:
        sys.exit(f"expected one built package, found {files}")
    package = files[0]
    info = {}
    pkginfo = subprocess.run(["bsdtar", "-xOf", package, ".PKGINFO"],
                             check=True, capture_output=True,
                             text=True).stdout
    for line in pkginfo.splitlines():
        if " = " in line and not line.startswith("#"):
            key, value = line.split(" = ", 1)
            info.setdefault(key, []).append(value)
    with open(package, "rb") as f:
        digest = hashlib.sha512(f.read()).hexdigest()
    filename = "telegram-desktop-export-$pkgver-$pkgrel-$CARCH.pkg.tar.zst"
    url = (f"https://github.com/{repo}/releases/download/"
           f"pkg-$pkgver-$pkgrel/{filename}")
    licenses = info.get("license", ["GPL-3.0-or-later WITH OpenSSL-exception"])
    text = (
        "# Maintainer: Remenod <remenod@gmail.com>\n"
        f"# Built from the telegram-desktop-export package by {repo}\n"
        "# (GitHub Actions, packaging branch) and published there.\n\n"
        f"pkgname={NAME}-bin\n"
        f"pkgver={pkgver}\n"
        f"pkgrel={pkgrel}\n"
        f"pkgdesc={quote(info['pkgdesc'][0])}\n"
        "arch=('x86_64')\n"
        f"url={quote(f'https://github.com/{repo}')}\n"
        + array("license", licenses)
        + array("depends", info.get("depend", []))
        + array("optdepends", info.get("optdepend", []))
        + "provides=('telegram-desktop' 'telegram-desktop-export')\n"
        "conflicts=('telegram-desktop' 'telegram-desktop-export')\n"
        "options=('!strip' '!debug')\n"
        f'source_x86_64=("{url}")\n'
        f'noextract=("{filename}")\n'
        f"sha512sums_x86_64=({quote(digest)})\n\n"
        "package() {\n"
        f'  bsdtar -xf "$srcdir/{filename}" -C "$pkgdir" \\\n'
        "    --exclude=.PKGINFO --exclude=.BUILDINFO --exclude=.MTREE \\\n"
        "    --exclude=.INSTALL\n"
        "}\n")
    target = os.path.join(out, f"{NAME}-bin")
    os.makedirs(target, exist_ok=True)
    with open(os.path.join(target, "PKGBUILD"), "w") as f:
        f.write(text)
    with open(os.path.join(target, "aur-files"), "w") as f:
        f.write("PKGBUILD\n.SRCINFO\n")
    print(f"{target}/PKGBUILD ready for {filename}")


if __name__ == "__main__":
    main()
