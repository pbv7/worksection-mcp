# Maintainers Guide

Repository maintainer playbook: dependency updates, release procedure, CHANGELOG
conventions, and rollback. End-user documentation lives in [README.md](README.md);
day-to-day code guidance lives in [CLAUDE.md](CLAUDE.md).

## Contents

- [Dependency Updates](#dependency-updates)
- [The P7D Supply-Chain Quarantine](#the-p7d-supply-chain-quarantine)
- [Release Procedure](#release-procedure)
- [CHANGELOG Convention](#changelog-convention)
- [Rolling Back a Release](#rolling-back-a-release)

## Dependency Updates

The project uses [uv](https://github.com/astral-sh/uv) exclusively. **Never** use `pip`,
and **never** manually edit `uv.lock`.

### Routine bump (no security pressure)

The Makefile wraps the common cases:

```bash
make deps-upgrade-runtime   # bump lower bounds for runtime deps in pyproject.toml
make deps-upgrade-dev       # bump lower bounds for dev deps in pyproject.toml
make deps-upgrade           # runtime + dev + uv lock --upgrade + uv sync + make check
```

For surgical bumps:

```bash
uv add <pkg>@latest                   # bump a runtime dep
uv add --optional dev <pkg>@latest    # bump a dev dep
uv lock --upgrade-package <pkg>       # upgrade one package without touching others
uv lock --upgrade                     # bump everything within current pyproject bounds
uv sync --frozen --extra dev          # install from the new lockfile
make check                            # verify CI-equivalent checks still pass
```

Document every bump (runtime, dev, transitive of note) under `## [Unreleased]` in
`CHANGELOG.md` at the time of commit — see [CHANGELOG Convention](#changelog-convention).

### Security-driven bump

When a CVE drops:

1. Read the advisory — confirm the patched version and the affected range.
2. `uv lock --upgrade-package <pkg>` and verify the new version is `>=` the patched version.
3. If uv pulls a version *below* the patched floor, the patched release is likely inside
   the **P7D quarantine** — see the next section before doing anything else.
4. Run `make check`. If anything breaks, fix forward — never downgrade past a known CVE.
5. Categorize the CHANGELOG entry under `### Security` with the CVE/GHSA identifier and
   patched version. Example:

   ```text
   ### Security
   - authlib 1.6.11 → 1.7.2
     (MEDIUM: CVE-2026-44681 / GHSA-r95x-qfjj-fjj2 — OIDC implicit/hybrid flow open
     redirect; patched in 1.6.12)
   ```

## The P7D Supply-Chain Quarantine

`uv.lock` has `exclude-newer-span = "P7D"` at the top — uv refuses to resolve to any
package version uploaded to PyPI in the last 7 days. This is a defense against malicious
fresh releases (compromised maintainer accounts, typosquats published moments before).
uv recalculates `exclude-newer` automatically on every lock; **don't touch it by hand**.

### How the gotcha shows up

If a CVE patch was released within the last week, `uv lock --upgrade-package <pkg>` will
silently keep the older, vulnerable version pinned. You will see no error — just no
upgrade. Check by greping for the package in `uv.lock` and comparing against the advisory.

### Why you should not bypass it

uv offers `--exclude-newer-package <pkg>=<timestamp>` to override the quarantine for one
package. **Do not use it for a release commit.** Mechanics:

- The override persists into `uv.lock` under `[options.exclude-newer-package]`.
- `uv run` re-resolves on invocation and treats lockfile options as *derived* from
  current config (CLI flags, env vars, `[tool.uv]` in `pyproject.toml`). If the override
  is in none of those, uv strips it and re-resolution fails with `No solution found`.
- Putting `[tool.uv] exclude-newer-package = { ... }` in `pyproject.toml` makes the
  override permanent — pollutes project config with per-package security exceptions and
  defeats the purpose of P7D for that package going forward.

**Project policy: no persistent `--exclude-newer-package` overrides anywhere
(pyproject, uv.lock, or otherwise). Either wait for the quarantine to lift, or hold the
release.**

### The right move: wait

A package published at time `T` becomes resolvable at `T + 7 days`. The wait is bounded
and visible. To compute time-to-lift:

```bash
# Inspect upload time of the patched version in uv.lock or PyPI
# (uv.lock records `upload-time` on every wheel entry)
grep -A4 '^name = "<pkg>"' uv.lock | grep upload-time

# Compute hours remaining
python3 -c "from datetime import datetime, timezone; \
  lift = datetime.fromisoformat('<upload-iso>'.replace('Z','+00:00')) + \
         __import__('datetime').timedelta(days=7); \
  print(f'lifts at {lift.isoformat()}; wait {(lift - datetime.now(timezone.utc)).total_seconds()/3600:.1f}h')"
```

After the lift, plain `uv lock --upgrade-package <pkg>` picks the patched version.

### If you genuinely cannot wait

Hold the release. Document the open CVE in CHANGELOG (under `### Security` of
`[Unreleased]` with a note like "*pending P7D quarantine lift on YYYY-MM-DD*") and cut
the release once uv can resolve the patched version cleanly. Don't ship the bulk of the
release without the security fix you came for — that's worse than holding.

## Release Procedure

Releases are fully manual on `main`. CI (`release.yml`) triggers on a pushed `v*` tag,
builds the package with `uv build`, and creates a GitHub Release with auto-generated
notes and `dist/*` assets attached. There is no PyPI publish step.

To cut a release after merging changes to `main`:

1. **`pyproject.toml`** — bump `version = "x.y.z"`.
2. **`uv.lock`** — run `uv lock` to record the new project version.
3. **`CHANGELOG.md`** — promote `[Unreleased]` → `[x.y.z] - YYYY-MM-DD`; add the
   comparison link at the bottom (`[x.y.z]: https://github.com/pbv7/worksection-mcp/compare/vA.B.C...vx.y.z`).
4. **`SECURITY.md`** — update the Supported Versions table only on minor/major bumps
   (e.g. `0.5.x` → `0.6.x`). Patch releases don't change support scope.
5. Commit: `chore(release): bump to vx.y.z`. Push to `main`.
6. Tag and push the tag:

   ```bash
   git tag vx.y.z
   git push origin vx.y.z
   ```

   Pushing the tag triggers `release.yml` which builds + attaches `dist/*` to a new
   GitHub Release with auto-generated notes.

Verify after the workflow completes:

```bash
gh run list --workflow=release.yml --limit 1   # green
gh release view vx.y.z --json tagName,assets   # 3 assets attached
```

## CHANGELOG Convention

All changes — features, fixes, deps, docs — go under `## [Unreleased]` as they are
committed, regardless of whether they are part of a planned release. **Do not** write
to a versioned section (e.g. `[0.6.0]`) until the `chore(release)` commit. The release
commit is the single moment that promotes `[Unreleased]` to a versioned entry.

Sections, in this order when present:

- `### Security` — CVE patches and vulnerability fixes; include CVE/GHSA + patched version
- `### Added` — new user-facing features
- `### Changed` — modifications to existing behavior, routine dep bumps without CVE
- `### Fixed` — bug fixes
- `### Removed` — removed features, deps, or settings

Follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/). The
markdownlint config allows duplicate `### Security` (etc.) headings across versions
via `MD024 siblings_only`.

## Rolling Back a Release

If a release goes out wrong — bad version, missing fix, broken workflow — a clean
rollback is preferable to leaving the bad release published. Rollback is destructive
across both git history and GitHub Releases; do it deliberately.

### Steps

```bash
# 1. Discard local uncommitted changes that belong to the bad release
git restore <files>

# 2. Delete the GitHub Release and its tag (in one call)
gh release delete vX.Y.Z --yes --cleanup-tag

# 3. Belt-and-braces: ensure the tag is gone everywhere
git tag -d vX.Y.Z 2>/dev/null
git ls-remote --tags origin vX.Y.Z   # expect empty

# 4. Force-reset main to the last good commit
git reset --hard <last-good-sha>
git push --force-with-lease origin main
# (Branch protection bypass is required on main and only the repo owner can do this.)
```

### What you cannot remove

- **Workflow run history.** The bad `release.yml` run stays in `gh run list` forever.
  `gh run delete <id>` hides it from the default UI list but does not erase audit logs.
- **Anyone who already downloaded the release artifacts.** Since this project does not
  publish to PyPI, the blast radius is small (only GitHub Release asset downloaders).

### When not to roll back

- Users have already pulled the artifacts in volume. Roll forward with a patch release
  fixing the issue instead.
- The bad release contained important fixes that other people may depend on. Cut a new
  patch that addresses the regression rather than rewinding.

### Discoverability

After rollback, the orphan workflow run (success status, but pointing at a deleted tag)
will sit in `gh run list` until you delete it. Include this in the cleanup step of the
follow-up release.
