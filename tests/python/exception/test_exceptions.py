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
import pytest

from gsm_data_generator.exception.exceptions import (
    NoCardError,
    NoJsonFilePresent,
    NoSettingsFilePresent,
    NoTemplateFilePresent,
    ProtocolError,
    ReaderError,
    SwMatchError,
)
from gsm_data_generator.error import (
    DATAGENError,
    DiagnosticError,
    InternalError,
    OpAttributeInvalid,
    OpAttributeRequired,
    OpAttributeUnImplemented,
    OpError,
    OpNotImplemented,
    RPCError,
    RPCSessionTimeoutError,
)

_SIMPLE_EXCEPTIONS = [
    NoSettingsFilePresent,
    NoTemplateFilePresent,
    NoJsonFilePresent,
    NoCardError,
    ProtocolError,
    ReaderError,
]

_DATAGEN_EXCEPTIONS = [
    DATAGENError,
    InternalError,
    RPCError,
    RPCSessionTimeoutError,
    OpError,
    OpNotImplemented,
    OpAttributeRequired,
    OpAttributeInvalid,
    OpAttributeUnImplemented,
    DiagnosticError,
]


# ------------------------------------------------------------------ #
# Simple exceptions (pySim-derived)
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("exc_class", _SIMPLE_EXCEPTIONS)
def test_simple_exceptions_can_be_raised_and_caught(exc_class):
    with pytest.raises(exc_class):
        raise exc_class("test message")


@pytest.mark.parametrize("exc_class", _SIMPLE_EXCEPTIONS)
def test_simple_exceptions_inherit_from_exception(exc_class):
    assert issubclass(exc_class, Exception)


@pytest.mark.parametrize("exc_class", _SIMPLE_EXCEPTIONS)
def test_simple_exceptions_carry_message(exc_class):
    try:
        raise exc_class("detail message")
    except exc_class as e:
        assert "detail message" in str(e)


# ------------------------------------------------------------------ #
# SwMatchError
# ------------------------------------------------------------------ #

def test_sw_match_error_str_without_rs():
    err = SwMatchError("9000", "9001")
    result = str(err)
    assert "9000" in result
    assert "9001" in result
    assert "failed" in result.lower()


def test_sw_match_error_str_with_none_rs():
    err = SwMatchError("6700", "9000", rs=None)
    result = str(err)
    assert "6700" in result
    assert "9000" in result


def test_sw_match_error_stores_sw_actual():
    err = SwMatchError("6F00", "9000")
    assert err.sw_actual == "6F00"


def test_sw_match_error_stores_sw_expected():
    err = SwMatchError("6F00", "9000")
    assert err.sw_expected == "9000"


def test_sw_match_error_is_exception():
    err = SwMatchError("9000", "9001")
    assert isinstance(err, Exception)


def test_sw_match_error_can_be_caught_as_exception():
    with pytest.raises(Exception):
        raise SwMatchError("9000", "9001")


# ------------------------------------------------------------------ #
# DATAGEN error hierarchy
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("exc_class", _DATAGEN_EXCEPTIONS)
def test_datagen_exceptions_can_be_raised(exc_class):
    with pytest.raises(exc_class):
        raise exc_class("test")


def test_internal_error_is_datagen_error():
    assert issubclass(InternalError, DATAGENError)


def test_rpc_error_is_datagen_error():
    assert issubclass(RPCError, DATAGENError)


def test_rpc_session_timeout_is_rpc_error():
    assert issubclass(RPCSessionTimeoutError, RPCError)


def test_rpc_session_timeout_is_also_timeout_error():
    assert issubclass(RPCSessionTimeoutError, TimeoutError)


def test_op_error_is_datagen_error():
    assert issubclass(OpError, DATAGENError)


def test_op_not_implemented_is_also_not_implemented_error():
    assert issubclass(OpNotImplemented, NotImplementedError)


def test_op_attribute_required_is_also_attribute_error():
    assert issubclass(OpAttributeRequired, AttributeError)


def test_op_attribute_invalid_is_also_attribute_error():
    assert issubclass(OpAttributeInvalid, AttributeError)


def test_op_attribute_unimplemented_is_also_not_implemented_error():
    assert issubclass(OpAttributeUnImplemented, NotImplementedError)


def test_diagnostic_error_is_datagen_error():
    assert issubclass(DiagnosticError, DATAGENError)


def test_datagen_error_is_runtime_error():
    assert issubclass(DATAGENError, RuntimeError)


def test_catch_internal_as_datagen_error():
    with pytest.raises(DATAGENError):
        raise InternalError("something went wrong internally")


def test_catch_op_error_as_datagen_error():
    with pytest.raises(DATAGENError):
        raise OpAttributeInvalid("bad attribute value")
