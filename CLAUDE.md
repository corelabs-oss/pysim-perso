# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Python library for generating and processing GSM/USIM/eSIM SIM card datasets. It generates cryptographic SIM parameters (Ki, OPC, eKI, ACC, PIN/PUK) and transforms them into operator-specific output formats.

## Commands

```bash
# Install
python setup.py install
pip install -e .          # editable/dev install
pip install -e ".[test]"  # with test extras

# Tests
pytest --maxfail=1 --disable-warnings -v   # matches CI
pytest tests/python/algorithm/test_encrypt.py -v  # single module

# Type checking
mypy gsm_data_generator/

# Pre-commit hooks (includes Black, MyPy, ASF header checks)
pre-commit install --hook-type pre-push
pre-commit run --all-files
```

## Architecture

The library is organized into independent sub-packages under `gsm_data_generator/`:

- **`algorithm/`** — Crypto primitives. `CryptoUtils` does raw AES-128 CBC (zero IV) and XOR. `DependentDataGenerator` wraps these to produce OPC (`AES_K(OP) ⊕ OP`), eKI (encrypted Ki), and ACC (bitmask from last IMSI digit).

- **`generator/`** — `DataGenerator` produces random SIM secrets using `secrets.token_hex` / `secrets.SystemRandom`. All values are returned as uppercase hex strings.

- **`globals/parameters.py`** — `Parameters` is a thread-safe singleton (extends `DataFrames` singleton) that holds all in-flight SIM parameters (ICCID, IMSI, Ki, OPC, PIN/PUK, etc.) and the three output DataFrames (ELECT, GRAPH, SERVER). Access via `Parameters.get_instance()`.

- **`processor/`** — Stateless utilities: `DataProcessing` for range parsing and deduplication, `DataFrameProcessor` for pandas DataFrame column operations.

- **`error.py` / `exception/`** — Custom exception hierarchy rooted at `DATAGENError`. `DiagnosticError` suppresses backtraces by default; set `DATAGEN_BACKTRACE=1` to see them. The `__init__.py` wraps `sys.excepthook` to terminate active child processes on exception.

## Non-Obvious Things

- **Commented dead code**: Large blocks of commented-out code exist throughout (especially `parameters.py` and `algorithm/encrypt.py`). The old setter/getter pattern was replaced with `@property`, but old methods remain commented inline. Don't mistake them for documentation.

- **`setup.py` uses `exec` to read `libinfo.py`**: It cannot `import` the package because `__init__.py` pulls in dependencies not yet installed at setup time. This is intentional.

- **All source files require ASF license headers**: The pre-commit hook enforces Apache 2.0 headers. New files must include the header or the hook will fail.

- **Windows test exclusions**: `tests/python/conftest.py` skips several frontend test paths on Windows. These paths don't exist in this repo (they're inherited from an upstream template); the exclusions are harmless.

- **`executor/script_gpt.py`** is experimental/incomplete. Don't treat it as stable API.
