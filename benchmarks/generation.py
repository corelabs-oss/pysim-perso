# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Measure generation throughput, and prove a change did not alter output.

    python benchmarks/generation.py                    # throughput
    python benchmarks/generation.py -n 100000 -r 5     # bigger, more repeats
    python benchmarks/generation.py --profile          # where the time goes
    python benchmarks/generation.py --compare main     # A/B against a git ref
    python benchmarks/generation.py --verify main      # byte-identical output?

``--compare`` and ``--verify`` check the ref out into a throwaway git worktree
and re-run this same script against that copy of the package, so they work
even for refs predating this file.

Timings are best-of-N, not a mean: the minimum is the run least disturbed by
other load, which is what you want when comparing two implementations.
"""

import argparse
import cProfile
import io
import itertools
import json
import pstats
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "settings.example.json"


class DeterministicGenerator:
    """Counter-backed stand-in for :class:`DataGenerator`.

    Generation is otherwise seeded from the OS CSPRNG, so two runs never agree.
    Substituting this makes a run reproducible, which is what lets --verify
    diff two implementations. Never use it to produce real cards.
    """

    def __init__(self):
        self._counter = itertools.count()

    def generate_ki(self) -> str:
        return f"{next(self._counter):032X}"

    def generate_otas(self) -> str:
        return f"{next(self._counter):032X}"

    def generate_k4(self, length: int) -> str:
        return f"{next(self._counter):0{length * 2}X}"

    def generate_4_digit(self) -> str:
        return f"{next(self._counter) % 10000:04d}"

    def generate_8_digit(self) -> str:
        return f"{next(self._counter) % 100000000:08d}"


def build_script(root: Path, size: int, deterministic: bool):
    """Import the package under *root* and return a configured script."""
    sys.path.insert(0, str(root))
    from pysim_perso import DataGenerationScript, json_loader_2_ConfigHolder

    config = json.loads(DEFAULT_CONFIG.read_text())
    config["DISP"]["size"] = size
    # Exercise every output; the default config leaves SERVER off.
    config["DISP"]["elect_check"] = True
    config["DISP"]["graph_check"] = True
    config["DISP"]["server_check"] = True
    config["PATHS"]["OUTPUT_FILES_DIR"] = tempfile.mkdtemp(prefix="pysim-bench-")

    script = DataGenerationScript(
        json_loader_2_ConfigHolder(config),
        data_generator=DeterministicGenerator() if deterministic else None,
    )
    script.json_to_global_params()
    return script


def measure(root: Path, size: int, repeats: int) -> float:
    """Return the best wall-clock time over *repeats* generation runs."""
    best = None
    for _ in range(repeats):
        script = build_script(root, size, deterministic=False)
        start = time.perf_counter()
        script.generate_all_data()
        elapsed = time.perf_counter() - start
        best = elapsed if best is None else min(best, elapsed)
    return best


def dump_output(root: Path, size: int) -> str:
    """Serialise a deterministic run, for comparing two implementations."""
    script = build_script(root, size, deterministic=True)
    frames, keys = script.generate_all_data()
    parts = [json.dumps(keys, sort_keys=True)]
    for name in sorted(frames):
        parts.append(f"### {name}")
        parts.append(frames[name].to_csv(index=False))
    return "\n".join(parts)


def worktree(ref: str):
    """Check *ref* out into a temporary worktree, yielding its path."""
    path = Path(tempfile.mkdtemp(prefix=f"pysim-{ref.replace('/', '-')}-"))
    subprocess.run(
        ["git", "worktree", "add", "--quiet", "--detach", str(path), ref],
        cwd=REPO_ROOT,
        check=True,
    )
    return path


def remove_worktree(path: Path) -> None:
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(path)],
        cwd=REPO_ROOT,
        check=False,
    )


def run_in(root: Path, args: list) -> str:
    """Run this script against the package under *root*, in a fresh process."""
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--root", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout


def report(size: int, seconds: float, label: str) -> None:
    print(f"{label:<12} {seconds:6.2f}s   {size / seconds:>9,.0f} cards/s")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", "--size", type=int, default=50_000, help="cards")
    parser.add_argument("-r", "--repeats", type=int, default=3, help="timed runs")
    parser.add_argument("--profile", action="store_true", help="cProfile one run")
    parser.add_argument("--compare", metavar="REF", help="A/B against a git ref")
    parser.add_argument("--verify", metavar="REF", help="diff output vs a git ref")
    parser.add_argument("--root", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--dump", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    root = args.root or REPO_ROOT

    # Child-process modes, used by --compare and --verify.
    if args.dump:
        print(dump_output(root, args.size), end="")
        return 0
    if args.root and not (args.profile or args.compare or args.verify):
        print(f"{measure(root, args.size, args.repeats):.6f}")
        return 0

    if args.verify:
        path = worktree(args.verify)
        try:
            theirs = run_in(path, ["--dump", "-n", str(args.size)])
            mine = dump_output(REPO_ROOT, args.size)
        finally:
            remove_worktree(path)
        if theirs == mine:
            print(f"output identical to {args.verify} ({len(mine):,} bytes)")
            return 0
        print(f"OUTPUT DIFFERS from {args.verify}", file=sys.stderr)
        for n, (a, b) in enumerate(zip(theirs.splitlines(), mine.splitlines())):
            if a == b:
                continue
            # Window the excerpt around the first differing character;
            # printing from column 0 usually shows two identical prefixes.
            column = next(
                (i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b))
            )
            start = max(0, column - 30)
            width = len(f"{args.verify}: ")
            print(f"  line {n + 1}, column {column + 1}:", file=sys.stderr)
            print(f"    {args.verify}: ...{a[start : column + 30]}", file=sys.stderr)
            print(
                f"    {'working tree':<{width - 2}}: ...{b[start : column + 30]}",
                file=sys.stderr,
            )
            print(f"    {' ' * (width + 3 + column - start)}^", file=sys.stderr)
            break
        return 1

    if args.compare:
        path = worktree(args.compare)
        try:
            theirs = float(
                run_in(path, ["-n", str(args.size), "-r", str(args.repeats)])
            )
        finally:
            remove_worktree(path)
        mine = measure(REPO_ROOT, args.size, args.repeats)
        print(f"{args.size:,} cards, best of {args.repeats}\n")
        report(args.size, theirs, args.compare)
        report(args.size, mine, "working tree")
        print(f"\nspeedup: {theirs / mine:.2f}x")
        return 0

    if args.profile:
        script = build_script(root, args.size, deterministic=False)
        profiler = cProfile.Profile()
        profiler.enable()
        script.generate_all_data()
        profiler.disable()
        stream = io.StringIO()
        pstats.Stats(profiler, stream=stream).sort_stats("tottime").print_stats(15)
        print(stream.getvalue())
        print("Note: profiling roughly triples wall time; ignore the totals here")
        print("and take throughput from a run without --profile.")
        return 0

    report(args.size, measure(root, args.size, args.repeats), "working tree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
