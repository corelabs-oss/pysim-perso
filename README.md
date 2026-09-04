<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/corelabs-aperture-bone.svg">
    <img src="docs/corelabs-aperture-ink.svg" alt="corelabs-oss" width="96">
  </picture>
</p>

<h1 align="center">pysim-perso</h1>

<p align="center">
  <a href="https://github.com/corelabs-oss/pysim-perso/actions/workflows/ci.yml"><img src="https://github.com/corelabs-oss/pysim-perso/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/pysim-perso/"><img src="https://img.shields.io/pypi/v/pysim-perso" alt="PyPI"></a>
  <a href="https://pypi.org/project/pysim-perso/"><img src="https://img.shields.io/pypi/pyversions/pysim-perso" alt="Python versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-green" alt="License"></a>
</p>

pysim-perso produces the per-card material a SIM personalization run requires —
identifiers, authentication keys and administrative codes — from a single
declarative configuration, and emits it in the formats consumed by
personalization equipment, laser marking systems and network provisioning.

It is intended for SIM manufacturers, MVNOs and test-lab engineers who need
reproducible, standards-conformant batches without maintaining bespoke scripts
per operator.

## Installation

Requires Python 3.10 or newer.

```bash
pip install pysim-perso
```

Runtime dependencies (`pandas`, `pydantic`, `pycryptodome`, `numpy`) are
resolved automatically.

<details>
<summary>Installing from source</summary>

```bash
git clone https://github.com/corelabs-oss/pysim-perso.git
cd pysim-perso
pip install -e .
```

</details>

## Quick start

Copy the example configuration and set your operator parameters:

```bash
cp settings.example.json settings.json
```

At minimum, set `imsi`, `iccid`, `K4`, `op` and `size`.

```python
from pysim_perso import json_loader, DataGenerationScript

config = json_loader("settings.json")

script = DataGenerationScript(config)
script.json_to_global_params()

result_dfs, keys = script.generate_all_data()
print(result_dfs["ELECT"].head())      # pandas DataFrame, one row per SIM

written = script.write_outputs(result_dfs)
print(written["ELECT"])                # <OUTPUT_FILES_DIR>/<FILE_NAME>.txt
```

Each `DataGenerationScript` owns its own state, so independent configurations
can be generated concurrently in one process. Read a run's parameters through
`script.params`.

To confirm an installation end to end, including the TS 35.206 test vector:

```bash
python verify.py
```

Further runnable examples are in [`examples/`](examples/).

## What it generates

Each generated record describes one SIM card across 23 fields:

| Group | Fields | Derivation |
|---|---|---|
| Identifiers | `ICCID`, `IMSI` | Sequenced from a configured starting value |
| Authentication | `KI` | 128-bit random, from the OS CSPRNG |
| | `OPC` | `AES_Ki(OP) ⊕ OP` |
| | `EKI` | `AES_K4(Ki)` — Ki under the transport key |
| | `ACC` | Access control class bitmask, from the last IMSI digit |
| Cardholder | `PIN1`, `PIN2`, `PUK1`, `PUK2` | Fixed per batch or random per card |
| Administrative | `ADM1`, `ADM6` | Fixed per batch or random per card |
| OTA | `KIC1-3`, `KID1-3`, `KIK1-3` | 128-bit random per card |
| Operator | `OP`, `K4` | Constant across the batch, from configuration |

### Standards

| Area | Reference |
|---|---|
| OPc derivation | 3GPP TS 35.206 (MILENAGE) |
| `EF_IMSI`, `EF_ICCID`, `EF_ACC` encoding | 3GPP TS 31.102 |
| Access control classes | 3GPP TS 22.011 |
| ICCID numbering and check digit | ITU-T E.118 (Luhn) |
| OTA keysets | ETSI TS 102 225 |

The OPc implementation is verified against the TS 35.206 test vector on every
CI run.

## Output formats

Three outputs are produced, each enabled independently and written with its own
column separator:

| Output | Consumer | Encoding | File |
|---|---|---|---|
| `ELECT` | Personalization equipment | Fields encoded to their EF representation | `<FILE_NAME>.txt` |
| `SERVER` | HLR/HSS provisioning | Plain values | `<FILE_NAME>_server.txt` |
| `GRAPH` | Laser marking | Plain values, clipped to print positions | `<FILE_NAME>_<OUTPUT_FILES_LASER_EXT>.txt` |

`ELECT` applies GSM EF encoding: nibble-swapped ICCID with its Luhn check
digit, length- and parity-prefixed IMSI, and `0xFF`-padded PIN.

## Configuration

A single JSON document with three sections. All fields are validated on load;
invalid values raise a `ValidationError` naming the offending field rather than
failing later in the pipeline.

### `DISP` — generation parameters

| Field | Type | Description |
|---|---|---|
| `imsi` | 15 digits | Starting IMSI. See [Identifier sequencing](#identifier-sequencing) |
| `iccid` | 18–19 digits | Starting ICCID, **without** the Luhn check digit — it is computed during encoding |
| `op` | 32 hex chars | Operator key |
| `K4` | 32, 48 or 64 hex chars | Transport key. Length selects the AES variant: 128, 192 or 256 |
| `size` | 1–1,000,000 | Number of cards in the batch |
| `pin1`, `pin2` | 4 digits | PIN value, used when the corresponding `*_fix` flag is set |
| `puk1`, `puk2` | 8 digits | PUK value, same convention |
| `adm1`, `adm6` | 8 printable ASCII | Administrative codes, same convention |
| `pin1_fix`, `puk1_fix`, `adm1_fix`, … | bool | `true` applies the configured value to every card; `false` generates a unique random value per card |
| `elect_check`, `graph_check`, `server_check` | bool | Enable each output |
| `elect_data_sep`, `server_data_sep`, `graph_data_sep` | string | Column separator per output |
| `prod_check` | bool | Validate every parameter before generating. Raises `ConfigValidationError` listing all failures |

### `PATHS` — output locations

| Field | Description |
|---|---|
| `FILE_NAME` | Base name for output files, without extension |
| `OUTPUT_FILES_DIR` | Destination directory, created if absent. Also holds the issuance ledger |
| `OUTPUT_FILES_LASER_EXT` | Suffix distinguishing the laser output file |

### `PARAMETERS` — column selection

| Field | Description |
|---|---|
| `data_variables` | Ordered columns for `ELECT` |
| `server_variables` | Ordered columns for `SERVER` |
| `laser_variables` | Print position → `[column, type, "start-end"]` for `GRAPH` |

Valid column names, case-sensitive:

```
ICCID  IMSI  OP    K4    PIN1  PUK1  PIN2  PUK2  KI    EKI   OPC   ADM1
ADM6   ACC   KIC1  KID1  KIK1  KIC2  KID2  KIK2  KIC3  KID3  KIK3
```

`laser_variables` maps a print position to a slice of a field, so one column may
appear at several positions:

```json
"laser_variables": {
  "0": ["ICCID", "Normal", "0-3"],
  "1": ["ICCID", "Normal", "4-7"],
  "2": ["PIN1",  "Normal", "0-3"]
}
```

Keys are non-negative integers applied in ascending numeric order, independent
of their order in the file. Ranges are inclusive and must satisfy
`start <= end`.

## Identifier sequencing

`imsi` and `iccid` are sequenced as fixed-width digit strings rather than
integers, which preserves their structure:

- **Leading zeros are retained.** A test-network IMSI of `001010000000001`
  remains 15 digits across the batch.
- **The IMSI operator prefix is protected.** An IMSI is MCC (3 digits) + MNC
  (2–3) + MSIN, so only the trailing digits are incremented. A batch that would
  carry into the first five digits is rejected rather than silently reassigning
  cards to a different operator.
- **ICCID width is enforced.** A batch that would extend the ICCID beyond its
  configured length is rejected.

> [!NOTE]
> The five-digit protected prefix is a conservative bound valid under every
> numbering plan. Where the MNC is three digits, its final digit falls inside
> the incremented range and is not covered; keep such batches clear of the MSIN
> boundary.

## Issuance ledger

Re-running a configuration yields the **same** identifiers but **new** keys.
Two cards would then share an ICCID while holding different Ki values, and
neither could be provisioned reliably.

`write_outputs` records every issued range in `.issuance_ledger.json` within
`OUTPUT_FILES_DIR` and refuses any batch overlapping one already issued:

```
IssuanceOverlapError: ICCID range 8991…000-8991…009 overlaps batch 1
(8991…000-8991…009, issued 2026-08-08T09:14:22+00:00). Re-issuing would
produce duplicate ICCIDs with different Ki values.
```

Advance the starting identifiers to continue, or pass `check_issuance=False` to
override deliberately. A batch counts as issued when it is written, so
in-memory generation never consumes a range.

## Security considerations

This library produces live cryptographic key material. Treat its output as
secret.

- **Key generation** uses Python's `secrets` module, backed by the operating
  system CSPRNG. It is deliberately **not** seedable; a seeded generator may be
  injected via `DataGenerationScript(config, data_generator=…)` for reproducible
  test fixtures, and must never be used for cards intended for a real network.
- **Ki need not leave the process in the clear.** The `EKI` column carries Ki
  encrypted under the transport key `K4`; prefer it over `KI` in any output that
  leaves your control.
- **Output files are written unencrypted** with default permissions. Place
  `OUTPUT_FILES_DIR` on protected storage and handle transfer out of band.
- **Configuration contains `op` and `K4`.** Do not commit a populated
  `settings.json`; the repository tracks only `settings.example.json`.

## Public API

```python
from pysim_perso import (
    DataGenerationScript,       # end-to-end pipeline
    json_loader,                # load and validate configuration from a path
    json_loader_2_ConfigHolder, # ... from a dict or JSON string
    ConfigHolder,               # validated configuration
    OutputWriter,               # write frames to delimited files
    IssuanceLedger,             # issued-range tracking
    DataGenerator,              # random Ki, OTA keys, PIN/PUK
    DependentDataGenerator,     # OPc, eKI, ACC
    CryptoUtils,                # AES-CBC and XOR primitives
    EncodingUtils,              # GSM EF encode/decode
    DataTransform,              # hex, byte and nibble conversion
    DataProcessing,             # configuration and range parsing
    DataFrameProcessor,         # column construction and encoding
    Parameters, DataFrames,     # per-run state
    DATAGENError,               # base exception
    install_excepthook,         # opt-in diagnostic exception hook
)
```

Importing the library has no global side effects. `install_excepthook()` opts
into suppressed backtraces for `DiagnosticError` (unless `DATAGEN_BACKTRACE=1`)
and termination of multiprocessing children on an unhandled exception.

## Development

```bash
pip install -e .
pip install pytest pytest-cov black mypy pandas-stubs

pytest --maxfail=1 --disable-warnings -v          # full suite
pytest tests/python/algorithm/test_encrypt.py -v  # one module
pytest --cov=pysim_perso --cov-report=term-missing

black pysim_perso/ tests/python/ benchmarks/ verify.py setup.py
mypy pysim_perso/
```

### Benchmarking

`benchmarks/generation.py` measures generation throughput and, just as
importantly, proves a change did not alter output:

```bash
python benchmarks/generation.py                 # throughput, best of 3
python benchmarks/generation.py -n 200000 -r 5  # bigger batch, more repeats
python benchmarks/generation.py --profile       # where the time goes
python benchmarks/generation.py --compare main  # A/B against a git ref
python benchmarks/generation.py --verify main   # byte-identical output?
```

`--compare` and `--verify` check the ref out into a throwaway git worktree and
re-run the benchmark against that copy of the package, so they work against
refs that predate the benchmark itself.

Always pair a speedup with `--verify`. Generation draws from the OS CSPRNG, so
two runs never agree; `--verify` substitutes a counter-backed generator to make
runs reproducible, then diffs every output frame. A change that is faster and
silently wrong will pass the test suite.

`pandas-stubs` is required: `mypy.ini` sets `ignore_missing_imports = False`,
so unstubbed `pandas` is an error rather than a warning.

[CI](.github/workflows/ci.yml) runs black, mypy, the suite across Python
3.10–3.13 on Linux plus 3.11 on Windows and macOS, and a packaging job that
installs the built wheel into a clean environment and smoke-tests it. It also
runs weekly: dependencies are unpinned, so the scheduled run surfaces upstream
breakage without waiting for a change.

## Releasing

Versioning and the tag-driven release pipeline are described in
[RELEASING.md](RELEASING.md). Per-version changes are in
[CHANGELOG.md](CHANGELOG.md).

## Contributing

Issues and pull requests are welcome. Before opening a pull request, please
ensure `black`, `mypy` and the test suite pass locally — CI enforces all three.

New source files should carry the Apache-2.0 header used throughout the tree.

## License

Licensed under the [Apache License 2.0](LICENSE).
