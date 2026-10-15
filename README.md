# telegram-desktop-export

Telegram Desktop with patches for **Export Telegram data**, packaged for
Arch Linux and kept up to date automatically.

AUR packages:

- `telegram-desktop-export-bin` — the package built here (GitHub releases);
  updates install in a minute, like a stock binary package.
- `telegram-desktop-export` — the same PKGBUILD for building it yourself.

Both provide and conflict with `telegram-desktop`.

## What the patches change

1. **Media reuse between exports.** Every export writes `.media_index` into its
   folder. A new export reads the indexes of the exports next to it (the chosen
   folder and its `DataExport_*` / `ChatExport_*` subfolders) and hard-links a
   file already downloaded (copies it across disks) instead of downloading it
   again. Exports made by other clients have no index: their `result.json` is
   read and files are matched by chat, message id and role, only when the size
   on disk equals the size the server reports. Toggle: *Reuse media from
   previous exports*.
2. **No hangs on lost media.** File parts failing with temporary errors (5xx,
   timeouts) are retried 5 times with backoff, then the file is given up; a part
   without any answer for 45 s is requested once more, then given up — but only
   while the main connection is up, without a connection the export waits.
   Other per-file errors no longer abort the export. Given-up files are listed
   in `skipped_files.txt` in the export folder; running the export again fills
   the holes.
3. **Export panel in tiling window managers.** The progress panel no longer
   hides when it loses focus (with focus following the mouse it vanished at
   once); its window is titled `Telegram Desktop Export` for window rules.
4. **Size limit per media type** instead of one limit for all.
5. **Fix:** export settings with the *HTML and JSON* format were reset on every
   restart.

The patches are commits on the `export/v<version>` branches of this fork,
on top of upstream's release tags.

## How the automation works

`.github/workflows/packaging.yml` (this branch) runs every hour:

1. `scripts/check.py` — compares Arch Linux's `extra/telegram-desktop`
   (`pkgver-pkgrel`) with this repository's releases (`pkg-<pkgver>-<pkgrel>`).
   Arch is the trigger on purpose: its maintainers keep the build working for
   every release (TDLib commit, wallet-engine, dependencies), and it rebuilds
   the package when Qt and other libraries change, which a dynamically linked
   Telegram Desktop needs too.
2. `scripts/rebase.sh` — uses `export/v<pkgver>` if it exists, otherwise
   cherry-picks the newest `export/v*` branch onto the release tag and pushes
   it as `export/v<pkgver>`.
3. `scripts/make_pkgbuilds.py` — takes Arch's PKGBUILD of that exact version
   and changes only the name, provides/conflicts, `!lto`, and applies the patch
   in `prepare()`.
4. `scripts/build.sh` — builds it with makepkg in an `archlinux:base-devel`
   container; `scripts/make_bin_pkgbuild.py` writes the `-bin` PKGBUILD from
   the built package's `.PKGINFO`.
5. `scripts/release.sh` — publishes the package and the patch as GitHub release
   `pkg-<pkgver>-<pkgrel>`.
6. `scripts/publish_aur.sh` — pushes both AUR packages ("initial import",
   "update to <pkgver>-<pkgrel>"), with the dedicated key in secret
   `AUR_SSH_KEY`. Scheduled runs publish only when the repository variable
   `AUR_PUBLISH` is `true`; a manual run publishes when asked to.

A manual run with `republish=true` pushes the existing release of the current
Arch version to the AUR again without building (a few minutes), e.g. after a
failed push.

When a step fails, an issue *Build failed: <version>* is opened (or commented
on), and the AUR packages stay at the previous version. While that issue is
open, the hourly check doesn't retry the version (no repeated failures and
mail); a manual run with `force=true` or a newer Arch version builds again,
and a successful build closes the issue.

The repository allows local actions only, and `scripts/disable_upstream_workflows.py`
keeps upstream's own workflows (carried by the release-based branches)
disabled.

## When the patches don't apply

The issue lists the conflicting files. Port the patches by hand:

```sh
git fetch https://github.com/telegramdesktop/tdesktop.git tag v<new>
git switch -c export/v<new> v<new>
git cherry-pick v<old>..export/v<old>   # resolve, git cherry-pick --continue
git push origin export/v<new>
gh workflow run packaging.yml -f force=true -f publish=true
```

An existing `export/v<new>` branch is used as is.
