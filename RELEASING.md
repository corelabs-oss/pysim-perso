<!--- Licensed to the Apache Software Foundation (ASF) under one -->
<!--- or more contributor license agreements.  See the NOTICE file -->
<!--- distributed with this work for additional information -->
<!--- regarding copyright ownership.  The ASF licenses this file -->
<!--- to you under the Apache License, Version 2.0 (the -->
<!--- "License"); you may not use this file except in compliance -->
<!--- with the License.  You may obtain a copy of the License at -->
<!---   http://www.apache.org/licenses/LICENSE-2.0 -->
<!--- Unless required by applicable law or agreed to in writing, -->
<!--- software distributed under the License is distributed on an -->
<!--- "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY -->
<!--- KIND, either express or implied.  See the License for the -->
<!--- specific language governing permissions and limitations -->
<!--- under the License. -->

# Releasing

## Versioning

`pysim-perso` follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the standard pre-1.0 caveat: **while the major version is `0`, a minor
bump may contain breaking changes.** Read `0.x` as "the API is not settled
yet".

| Change | Bump |
| --- | --- |
| Breaking API change (removed/renamed public symbol, changed behaviour callers depend on) | minor while `0.x`, major from `1.0.0` |
| New feature, backwards compatible | minor |
| Bug fix, docs, packaging metadata | patch |

Pre-releases use PEP 440 suffixes — `1.2.0rc1`, `1.2.0b1`, `1.2.0.dev1`. The
release workflow detects them and marks the GitHub release as a pre-release so
it does not become "latest".

### Single source of truth

`pysim_perso/libinfo.py` holds `__version__` and **nothing else derives from
anywhere else**:

- `setup.py` execs `libinfo.py` to read it at build time (it cannot import the
  package, which would pull in pandas/pydantic before they are installed).
- `pysim_perso.__version__` re-exports it.
- The release workflow refuses to publish if the git tag disagrees with it.

To bump a version you edit exactly one line in `pysim_perso/libinfo.py`.

### Tag format

Going forward, tags are `vX.Y.Z` — for example `v0.0.4`.

Tags predating this convention are inconsistent (`0.0.1.dev0`,
`gsm_data_generator_v0.0.3`) and are left alone as historical record. Do not
create new tags in those shapes; the release workflow only triggers on `v*`.

## Cutting a release

Everything is automated from the tag. The steps are:

1. **Make sure `main` is green.** The release workflow rebuilds and re-verifies,
   but it does not run the lint/typecheck/test matrix — CI on `main` does.

2. **Bump the version.**

   ```bash
   $EDITOR pysim_perso/libinfo.py   # __version__ = "X.Y.Z"
   ```

3. **Update `CHANGELOG.md`.** Move the `## [Unreleased]` items into a new
   `## [X.Y.Z] - YYYY-MM-DD` section and add the link reference at the bottom.
   The workflow **fails** if there is no section matching the version being
   released — the section body becomes the GitHub release notes verbatim.

4. **Commit and merge** through a pull request as usual.

   ```bash
   git commit -am "Release X.Y.Z"
   ```

5. **Tag the merge commit on `main` and push the tag.**

   ```bash
   git checkout main && git pull
   git tag -a vX.Y.Z -m "pysim-perso X.Y.Z"
   git push origin vX.Y.Z
   ```

That push is the point of no return. The `Release` workflow then:

- asserts the tag matches `__version__` and that the changelog has a matching
  section;
- builds the sdist and wheel, runs `twine check --strict`, asserts the wheel is
  `py3-none-any`, installs it into a clean venv outside the source tree and
  runs `verify.py` against it;
- publishes to PyPI through Trusted Publishing;
- creates the GitHub release with the changelog section as its notes and the
  built artifacts attached.

### If something goes wrong

**A PyPI version number can never be reused.** Deleting a release on PyPI does
not free the number. If a bad artifact is published, yank it on PyPI and
release a new patch version — never try to re-upload.

A failed run *before* the `pypi` job is safe to retry: delete the tag locally
and remotely, fix the problem, re-tag.

```bash
git push --delete origin vX.Y.Z && git tag -d vX.Y.Z
```

## One-time PyPI setup (Trusted Publishing)

The release workflow authenticates to PyPI with a short-lived OIDC token, so
there is no API token stored in GitHub. This has to be configured once on PyPI
before the first release.

Because `pysim-perso` does not exist on PyPI yet, use a **pending** publisher —
it creates the project on first upload.

1. Sign in at <https://pypi.org> and go to **Your account → Publishing**
   (<https://pypi.org/manage/account/publishing/>).
2. Under **Add a new pending publisher**, choose GitHub and fill in:

   | Field | Value |
   | --- | --- |
   | PyPI Project Name | `pysim-perso` |
   | Owner | `corelabs-oss` |
   | Repository name | `pysim-perso` |
   | Workflow name | `release.yml` |
   | Environment name | `pypi` |

3. In GitHub, create the matching environment: **Settings → Environments →
   New environment**, named `pypi`. The environment name must match exactly or
   PyPI rejects the token.

   This is also the right place to add a **required reviewer**, which makes the
   publish step pause for a human approval before it uploads. Recommended.

All five fields must match the workflow exactly. A mismatch fails at the
publish step with an OIDC error, after the artifacts are already built — the
tag is fine to reuse at that point, since nothing reached PyPI.

## Verifying a release

```bash
pip install pysim-perso==X.Y.Z
python -c "import pysim_perso; print(pysim_perso.__version__)"
```
