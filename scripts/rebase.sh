#!/usr/bin/env bash
# Put the export patches onto Telegram Desktop release $PKGVER.
#
# If the fork has a branch export/v$PKGVER already (made here before, or
# fixed by hand after a conflict), it is used as is. Otherwise the commits
# of the newest export/v* branch are cherry-picked onto the release tag and
# pushed as export/v$PKGVER. The result is work/export-patches.patch.
set -euo pipefail
: "${PKGVER:?}" "${REPO:?}" "${GH_TOKEN:?}"

upstream=https://github.com/telegramdesktop/tdesktop.git
fork="https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git"
tag="v${PKGVER}"
branch="export/v${PKGVER}"

mkdir -p work
git init --quiet work/tdesktop
cd work/tdesktop
git config user.name Remenod
git config user.email remenod@gmail.com

if git ls-remote --exit-code --heads "$fork" "$branch" >/dev/null; then
  echo "using the existing $branch"
  git fetch --quiet --depth=50 "$fork" "refs/heads/$branch:refs/heads/$branch"
  git fetch --quiet --depth=1 "$upstream" "refs/tags/$tag:refs/tags/$tag"
else
  latest=$(git ls-remote --heads "$fork" 'export/v*' \
    | sed 's#.*refs/heads/##' | sort -V | tail -n 1)
  if [[ -z "$latest" ]]; then
    echo "no export/v* branch in the fork" >&2
    exit 1
  fi
  base="${latest#export/}"
  echo "moving the commits of $latest ($base) onto $tag"
  git fetch --quiet --depth=50 "$fork" "refs/heads/$latest:refs/heads/$latest"
  git fetch --quiet --depth=1 "$upstream" \
    "refs/tags/$base:refs/tags/$base" "refs/tags/$tag:refs/tags/$tag"
  git checkout --quiet -b "$branch" "$tag"
  if ! git cherry-pick "$base..$latest"; then
    {
      echo "The patches of \`$latest\` don't apply to \`$tag\`."
      echo
      echo "Conflicting files:"
      git diff --name-only --diff-filter=U | sed 's/^/- `/; s/$/`/'
      echo
      echo "Fix: make a branch \`$branch\` from \`$tag\` with the patches"
      echo "ported by hand, push it to this repository and run the workflow"
      echo "again; it uses an existing branch as is."
    } > ../failure.md
    git cherry-pick --abort
    exit 1
  fi
  if [[ -z "${DRY_RUN:-}" ]]; then
    git push --quiet "$fork" "$branch"
  fi
fi

git diff "$tag" "$branch" > ../export-patches.patch
echo "patch: $(git diff --shortstat "$tag" "$branch")"
