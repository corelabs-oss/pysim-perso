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
"""Writes generated output frames to separator-delimited text files.

The PATHS and separator settings have always been part of the configuration
schema; this module is what finally consumes them.
"""

from pathlib import Path
from typing import Dict

import pandas as pd


class OutputWriter:
    """Writes ELECT, SERVER and GRAPH frames to delimited text files.

    File names are derived from the configured base name:

    ==========  ==========================================
    Output      File name
    ==========  ==========================================
    ELECT       ``<FILE_NAME>.txt``
    SERVER      ``<FILE_NAME>_server.txt``
    GRAPH       ``<FILE_NAME>_<OUTPUT_FILES_LASER_EXT>.txt``
    ==========  ==========================================
    """

    def __init__(
        self,
        output_dir,
        file_name: str,
        laser_ext: str = "laser",
        separators: Dict[str, str] = None,
        include_header: bool = True,
        encoding: str = "utf-8",
    ):
        self.output_dir = Path(output_dir)
        self.file_name = file_name
        self.laser_ext = laser_ext
        self.separators = separators or {}
        self.include_header = include_header
        self.encoding = encoding

    def path_for(self, output_type: str) -> Path:
        """Return the file path this writer would use for `output_type`."""
        suffixes = {
            "ELECT": "",
            "SERVER": "_server",
            "GRAPH": f"_{self.laser_ext}" if self.laser_ext else "_graph",
        }
        if output_type not in suffixes:
            raise ValueError(
                f"Unknown output type {output_type!r}; "
                f"expected one of {', '.join(sorted(suffixes))}"
            )
        return self.output_dir / f"{self.file_name}{suffixes[output_type]}.txt"

    def write(self, result_dfs: Dict[str, pd.DataFrame]) -> Dict[str, Path]:
        """Write every frame in `result_dfs` and return the paths written."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        written = {}
        for output_type, df in result_dfs.items():
            path = self.path_for(output_type)
            separator = self.separators.get(output_type, ",")
            self._write_frame(df, path, separator)
            written[output_type] = path
        return written

    def _write_frame(self, df: pd.DataFrame, path: Path, separator: str) -> None:
        # Written row by row rather than via DataFrame.to_csv so that
        # multi-character separators are supported (to_csv requires a
        # single character) and so large frames stream instead of being
        # joined into one string first.
        with open(path, "w", encoding=self.encoding, newline="\n") as handle:
            if self.include_header:
                handle.write(separator.join(map(str, df.columns)) + "\n")
            for row in df.itertuples(index=False, name=None):
                handle.write(separator.join(map(str, row)) + "\n")


__all__ = ["OutputWriter"]
