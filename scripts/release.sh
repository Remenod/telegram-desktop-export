#!/usr/bin/env bash
# Publish the built package and the patch as GitHub release pkg-$PKGVER-$PKGREL
# (the tag points at the export/v$PKGVER branch), and close failure issues
# of this version.
set -euo pipefail
: "${PKGVER:?}" "${PKGREL:?}" "${REPO:?}"

tag="pkg-${PKGVER}-${PKGREL}"
dir="work/out/telegram-desktop-export"
package="$dir/telegram-desktop-export-${PKGVER}-${PKGREL}-x86_64.pkg.tar.zst"
test -f "$package"

if gh release view "$tag" --repo "$REPO" >/dev/null 2>&1; then
  gh release delete "$tag" --repo "$REPO" --yes --cleanup-tag
fi
gh release create "$tag" "$package" "$dir/export-patches.patch" \
  --repo "$REPO" \
  --target "export/v${PKGVER}" \
  --title "telegram-desktop-export ${PKGVER}-${PKGREL}" \
  --notes "Telegram Desktop ${PKGVER} with the export patches of branch \`export/v${PKGVER}\`, built from Arch Linux's extra/telegram-desktop ${PKGVER}-${PKGREL}. Install from the AUR: \`telegram-desktop-export-bin\` (this package) or \`telegram-desktop-export\` (build it yourself)."

title="Build failed: ${PKGVER}-${PKGREL}"
gh issue list --repo "$REPO" --state open --search "\"$title\" in:title" \
  --json number --jq '.[].number' | while read -r number; do
  gh issue close "$number" --repo "$REPO" --comment "Built in ${RUN_URL:-a later run}."
done
