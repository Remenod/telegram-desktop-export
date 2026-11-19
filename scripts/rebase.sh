#!/usr/bin/env bash
# Put the export patches onto Telegram Desktop release $PKGVER.
#
# If the fork has a branch export/v$PKGVER already (made here before, or
# fixed by hand after a conflict), it is used as is. Otherwise the commits
# of the newest export/v* branch are cherry-picked onto the release tag and
# pushed as export/v$PKGVER with the deploy key (secret PUSH_SSH_KEY). The
# result is work/export-patches.patch.
set -euo pipefail
: "${PKGVER:?}" "${REPO:?}" "${GH_TOKEN:?}"

upstream=https://github.com/telegramdesktop/tdesktop.git
fork="https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git"
tag="v${PKGVER}"
branch="export/v${PKGVER}"
known_hosts="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/github_known_hosts"

mkdir -p work
git init --quiet work/tdesktop
cd work/tdesktop
git config user.name Remenod
git config user.email remenod@gmail.com
# A background gc after one fetch may rewrite the shallow file while the
# next fetch reads it ("shallow file has changed since we read it").
git config gc.auto 0
git config maintenance.auto false

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
    # Upstream's history between two releases sometimes changes its
    # .github/workflows files, and GITHUB_TOKEN can never push such commits
    # ("refusing to allow a GitHub App to create or update workflow ...
    # without workflows permission"). The branch goes out over SSH with the
    # read-write deploy key of this repository (secret PUSH_SSH_KEY).
    : "${PUSH_SSH_KEY:?the deploy key secret PUSH_SSH_KEY is not set}"
    key=$(mktemp)
    trap 'rm -f "$key"' EXIT
    printf '%s\n' "$PUSH_SSH_KEY" > "$key"
    GIT_SSH_COMMAND="ssh -i $key -o IdentitiesOnly=yes -o UserKnownHostsFile=$known_hosts -o StrictHostKeyChecking=yes" \
      git push --quiet "git@github.com:${REPO}.git" "$branch"
  fi
fi

git diff "$tag" "$branch" > ../export-patches.patch
echo "patch: $(git diff --shortstat "$tag" "$branch")"
