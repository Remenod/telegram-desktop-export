#!/usr/bin/env bash
# Runs as root inside archlinux:base-devel with the workspace at /work.
# Builds telegram-desktop-export with makepkg as an unprivileged user, then
# writes .SRCINFO for it and the telegram-desktop-export-bin PKGBUILD made
# from the built package.
set -euo pipefail
out=/work/work/out

pacman -Syu --noconfirm --needed git python
useradd --create-home builder
echo 'builder ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/builder
sed -i "s/^#\?MAKEFLAGS=.*/MAKEFLAGS=\"-j$(nproc)\"/" /etc/makepkg.conf
chown -R builder: "$out"

cd "$out/telegram-desktop-export"
sudo -u builder makepkg --syncdeps --noconfirm --cleanbuild
sudo -u builder makepkg --printsrcinfo > .SRCINFO

python3 /work/packaging/scripts/make_bin_pkgbuild.py "$out"
cd "$out/telegram-desktop-export-bin"
chown -R builder: .
sudo -u builder makepkg --printsrcinfo > .SRCINFO

# The host runner (not root) uploads these.
chmod -R a+rX "$out"
