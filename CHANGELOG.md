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

# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html), with
the pre-1.0 caveat described in [RELEASING.md](RELEASING.md): while the major
version is `0`, the minor version may carry breaking changes.

## [Unreleased]

### Changed

- Reorganised `executor/script.py` so it reads in pipeline order — configure,
  validate, generate, write — under section headers matching those stages, and
  documented that lifecycle in the module and class docstrings. Collapsed the
  triplicated `generate_pin`/`generate_puk`/`generate_adm` bodies onto one
  `_fixed_or_random` helper, replaced the positional 4-tuples in
  `generate_all_data` with a named `_OutputSpec`, and lifted the OTA keyset
  column names to a module constant. No behaviour change: every public method
  keeps its name, signature and semantics.

### Removed

- Dead scaffolding inherited from the Apache TVM project this repository was
  started from, none of it reachable from the build:
  - `setup.py`: `get_lib_path()` (called a `find_lib_path` that `libinfo.py`
    never defined), `git_describe_version()` (read a `../version.py` that does
    not exist), `_remove_path()`, the unused `BinaryDistribution` class and
    `Extension` imports, `FFI_MODE`/`CONDA_BUILD`/`INPLACE_BUILD`, and a
    commented-out block referencing cutlass and 3rdparty paths. This also drops
    a `from distutils.core import setup` fallback that would fail outright on
    Python 3.12+, where `distutils` was removed.
  - `pysim_perso/.asf.yaml`: Apache infrastructure config describing TVM ("Open
    deep learning compiler stack"), listing TVM collaborators and TVM CI status
    checks. Inert here — ASF tooling only reads it at a repository root.
  - `pysim_perso/.pre-commit-config.yaml`: hooks invoking a `docker/lint.sh`
    that does not exist, plus cpplint and clang-format for a pure-Python
    project, pinned to Python 3.6.
  - `mypy.ini`: three `[mypy-python.tvm.*]` sections for modules not present.
  - `pysim_perso/error.py`: commented-out `@register_error` FFI decorators and
    a Sphinx `:ref:` to an `error-handling-guide` document that does not exist.

  No public API, runtime behaviour or packaging metadata changed.

## [0.0.4] - 2026-09-03

First release published to PyPI, under the new name.

### Changed

- **Renamed the library from `gsm-data-generator` to `pysim-perso`.** The
  import package is now `pysim_perso`; the distribution installed from PyPI is
  `pysim-perso`. Every import must be updated:

  ```python
  # before
  from gsm_data_generator import DataGenerationScript, json_loader
  # after
  from pysim_perso import DataGenerationScript, json_loader
  ```

  No public class, function or attribute was renamed — only the package path.
  `DATAGENError` and the `DATAGEN_BACKTRACE` / `DATAGEN_FFI` environment
  variables keep their names.
- Project URLs now point at `corelabs-oss/pysim-perso`, matching the
  repository's actual location.

### Added

- Declared support for Python 3.12 and 3.13 in the package classifiers. Both
  were already exercised by CI; only the metadata was missing.
- `project_urls` metadata (source, issues, changelog) for the PyPI sidebar.
- A `Release` workflow that builds, verifies and publishes to PyPI via
  Trusted Publishing on a `v*` tag, and opens the matching GitHub release.
- This changelog, and [RELEASING.md](RELEASING.md) describing the versioning
  and release process.

### Notes

- `gsm-data-generator` was never published to PyPI, so there is no package to
  migrate from and no stub release pointing here. Users of the old name
  installed from source.

## [0.0.3] - 2026-08-08

Released as `gsm_data_generator_v0.0.3`, source-only.

### Added

- Runnable examples covering the public API (`examples/`).
- Expanded documentation.

## [0.0.2] - 2025-08-17

Released as `0.0.2.dev0`, source-only.

## [0.0.1] - 2025-08-15

Released as `gsm_data_generator_v0.0.1.dev0`, source-only. Initial release.

[Unreleased]: https://github.com/corelabs-oss/pysim-perso/compare/v0.0.4...HEAD
[0.0.4]: https://github.com/corelabs-oss/pysim-perso/releases/tag/v0.0.4
[0.0.3]: https://github.com/corelabs-oss/pysim-perso/releases/tag/gsm_data_generator_v0.0.3
[0.0.2]: https://github.com/corelabs-oss/pysim-perso/releases/tag/0.0.2.dev0
[0.0.1]: https://github.com/corelabs-oss/pysim-perso/releases/tag/gsm_data_generator_v0.0.1.dev0
