from pydantic import BaseModel, Field, conint, constr, field_validator
from dataclasses import dataclass
from typing import List, Dict
import json
import re

from ..utils import DEFAULT_HEADER

# Column names that may appear in any output selection. Anything else would
# raise a KeyError deep inside the DataFrame stage, so reject it up front.
_VALID_COLUMNS = frozenset(DEFAULT_HEADER)

# K4 (transport key) must map onto a legal AES key size — 16, 24 or 32 bytes,
# i.e. 32, 48 or 64 hex characters. Intermediate lengths pass a naive
# min/max check but blow up inside the AES call with an opaque error.
_K4_HEX_LENGTHS = (32, 48, 64)

# A laser range is "<start>-<end>", both non-negative integers.
_RANGE_RE = re.compile(r"^(\d+)-(\d+)$")

# Printable ASCII only: DataTransform.s2h formats each character with "%02x",
# so any code point above 0x7E silently produces a wrong-length field.
_PRINTABLE_ASCII_8 = r"^[ -~]{8}$"


class DISP(BaseModel):
    elect_data_sep: str = Field(..., min_length=1)
    server_data_sep: str = Field(..., min_length=1)
    graph_data_sep: str = Field(..., min_length=1)
    K4: constr(pattern=r"^[0-9A-Fa-f]+$", min_length=32, max_length=64)  # type: ignore
    op: constr(pattern=r"^[0-9A-Fa-f]{32}$")  # type: ignore
    imsi: constr(pattern=r"^\d{15}$")  # type: ignore
    iccid: constr(pattern=r"^\d{18,19}$")  # type: ignore
    pin1: constr(pattern=r"^\d{4}$")  # type: ignore
    puk1: constr(pattern=r"^\d{8}$")  # type: ignore
    pin2: constr(pattern=r"^\d{4}$")  # type: ignore
    puk2: constr(pattern=r"^\d{8}$")  # type: ignore
    adm1: constr(pattern=_PRINTABLE_ASCII_8)  # type: ignore
    adm6: constr(pattern=_PRINTABLE_ASCII_8)  # type: ignore
    size: conint(ge=1, le=1000000)  # type: ignore
    prod_check: bool
    elect_check: bool
    graph_check: bool
    server_check: bool
    pin1_fix: bool
    puk1_fix: bool
    pin2_fix: bool
    puk2_fix: bool
    adm1_fix: bool
    adm6_fix: bool

    @field_validator("K4")
    @classmethod
    def _check_k4_length(cls, value: str) -> str:
        if len(value) not in _K4_HEX_LENGTHS:
            raise ValueError(
                f"K4 must be 32, 48 or 64 hex characters "
                f"(AES-128, AES-192 or AES-256 respectively); got {len(value)}"
            )
        return value


class PATHS(BaseModel):
    FILE_NAME: str
    OUTPUT_FILES_DIR: str
    OUTPUT_FILES_LASER_EXT: str


class PARAMETERS(BaseModel):
    server_variables: List[str]
    data_variables: List[str]
    laser_variables: Dict[str, List[str]]

    @field_validator("server_variables", "data_variables")
    @classmethod
    def _check_known_columns(cls, value: List[str], info) -> List[str]:
        unknown = [c for c in value if c not in _VALID_COLUMNS]
        if unknown:
            raise ValueError(
                f"{info.field_name} contains unknown column(s) {unknown}. "
                f"Valid columns: {', '.join(sorted(_VALID_COLUMNS))}"
            )
        return value

    @field_validator("laser_variables")
    @classmethod
    def _check_laser_variables(
        cls, value: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        for key, entry in value.items():
            where = f"laser_variables[{key!r}]"

            # Keys are print positions and are sorted numerically downstream.
            if not key.isdigit():
                raise ValueError(
                    f"{where}: key must be a non-negative integer position, "
                    f"got {key!r}"
                )
            if len(entry) != 3:
                raise ValueError(
                    f"{where}: expected exactly 3 elements "
                    f"[column, type, range], got {len(entry)}"
                )

            column, _kind, range_str = entry
            if column not in _VALID_COLUMNS:
                raise ValueError(
                    f"{where}: unknown column {column!r}. "
                    f"Valid columns: {', '.join(sorted(_VALID_COLUMNS))}"
                )

            match = _RANGE_RE.match(range_str)
            if match is None:
                raise ValueError(
                    f"{where}: range {range_str!r} must be '<start>-<end>' "
                    f"with non-negative integers"
                )
            left, right = int(match.group(1)), int(match.group(2))
            if left > right:
                raise ValueError(
                    f"{where}: range {range_str!r} is reversed "
                    f"(start {left} > end {right}); this would silently "
                    f"produce an empty field"
                )
        return value


class ConfigData(BaseModel):
    DISP: DISP
    PATHS: PATHS
    PARAMETERS: PARAMETERS


@dataclass
class ConfigHolder:
    DISP: DISP
    PATHS: PATHS
    PARAMETERS: PARAMETERS

    @classmethod
    def from_config(cls, config: ConfigData):
        return cls(DISP=config.DISP, PATHS=config.PATHS, PARAMETERS=config.PARAMETERS)


def json_loader(path: str) -> ConfigHolder:
    # Explicit encoding: the default is locale-dependent, so a config
    # containing non-ASCII would fail to load on Windows.
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    config = ConfigData(**data)
    config_holder = ConfigHolder.from_config(config)
    return config_holder


def json_loader_2_ConfigHolder(input_data: dict | str) -> ConfigHolder:
    if isinstance(input_data, str):
        try:
            data = json.loads(input_data)
        except json.JSONDecodeError as e:
            raise ValueError("Invalid JSON string provided.") from e
    elif isinstance(input_data, dict):
        data = input_data
    else:
        raise ValueError("Input must be a dictionary or JSON string.")

    # Validate and create ConfigData instance
    config = ConfigData(**data)
    # Create and return ConfigHolder instance
    return ConfigHolder.from_config(config)


def gui_loader(path) -> ConfigHolder:
    #    data = json.load(path)
    data = path
    config = ConfigData(**data)
    config_holder = ConfigHolder.from_config(config)
    return config_holder


__all__ = [
    "DISP",
    "PATHS",
    "PARAMETERS",
    "ConfigHolder",
    "json_loader",
    "json_loader_2_ConfigHolder",
    "gui_loader",
    "ConfigData",
]
