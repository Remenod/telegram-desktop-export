#!/usr/bin/env bash
# Push telegram-desktop-export and telegram-desktop-export-bin to the AUR
# with the dedicated CI key (secret AUR_SSH_KEY). Commits are written the
# way the maintainer writes them: "initial import", "update to X".
set -euo pipefail
: "${PKGVER:?}" "${PKGREL:?}" "${AUR_SSH_KEY:?}"

here=$(pwd)
mkdir -p ~/.ssh
printf '%s\n' "$AUR_SSH_KEY" > ~/.ssh/aur
chmod 600 ~/.ssh/aur
cp packaging/aur_known_hosts ~/.ssh/known_hosts
export GIT_SSH_COMMAND="ssh -i $HOME/.ssh/aur -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes"

for pkg in telegram-desktop-export telegram-desktop-export-bin; do
  src="$here/work/out/$pkg"
  dst="$here/work/aur-$pkg"
  git clone --quiet "ssh://aur@aur.archlinux.org/${pkg}.git" "$dst"
  cd "$dst"
  # The AUR repository holds only what aur-files lists.
  git rm -r --quiet --ignore-unmatch . >/dev/null
  while read -r name; do
    [[ -n "$name" ]] && cp "$src/$name" .
  done < "$src/aur-files"
  git add -A
  if git diff --cached --quiet; then
    echo "$pkg: nothing changed"
    cd "$here"
    continue
  fi
  if git rev-parse --verify --quiet HEAD >/dev/null; then
    message="update to ${PKGVER}-${PKGREL}"
  else
    message="initial import"
  fi
  git -c user.name=Remenod -c user.email=remenod@gmail.com \
    commit --quiet -m "$message"
  git push --quiet origin HEAD:master
  echo "$pkg: $message"
  cd "$here"
done
