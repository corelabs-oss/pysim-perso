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
# pylint: disable=invalid-name, exec-used
"""Setup script for pysim-perso."""

import os
import pathlib
import sys

from setuptools import find_packages, setup

CURRENT_DIR = os.path.dirname(__file__)


def get_version():
    """Read __version__ out of libinfo.py without importing the package.

    Importing pysim_perso here would pull in pandas/pydantic, which are
    not necessarily installed yet at setup time.
    """
    libinfo_py = os.path.join(CURRENT_DIR, "pysim_perso", "libinfo.py")
    libinfo = {"__file__": libinfo_py}
    exec(compile(open(libinfo_py, "rb").read(), libinfo_py, "exec"), libinfo, libinfo)
    return libinfo["__version__"]


__version__ = get_version()


def long_description_contents():
    with open(
        pathlib.Path(CURRENT_DIR).resolve() / "README.md", encoding="utf-8"
    ) as readme:
        description = readme.read()

    return description


# Temporarily add this directory to the path so we can import the requirements generator
# tool.
sys.path.insert(0, os.path.dirname(__file__))
import gen_requirements

sys.path.pop(0)

requirements = gen_requirements.join_requirements()
extras_require = {
    piece: deps
    for piece, (_, deps) in requirements.items()
    if piece not in ("all", "core")
}

setup(
    name="pysim-perso",
    version=__version__,
    description="pysim-perso: A library for generating and processing GSM/USIM/eSIM SIM card datasets",
    long_description=long_description_contents(),
    long_description_content_type="text/markdown",
    url="https://github.com/corelabs-oss/pysim-perso",
    download_url="https://github.com/corelabs-oss/pysim-perso",
    author="pysim-perso Contributors",
    project_urls={
        "Source": "https://github.com/corelabs-oss/pysim-perso",
        "Issues": "https://github.com/corelabs-oss/pysim-perso/issues",
        "Changelog": "https://github.com/corelabs-oss/pysim-perso/blob/main/CHANGELOG.md",
    },
    license="Apache-2.0",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Telecommunications Industry",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries",
        "Topic :: Communications :: Telephony",
    ],
    keywords="gsm usim esim sim card data generation telecom 3gpp",
    # match/case (globals/parameters.py) and PEP 604 unions (parser/utils.py)
    # are used at runtime, so 3.10 is the true minimum.
    python_requires=">=3.10",
    zip_safe=True,
    install_requires=requirements["core"][1],
    extras_require=extras_require,
    packages=find_packages(include=["pysim_perso", "pysim_perso.*"]),
    # Deliberately no distclass: this is a pure-Python package. Forcing a
    # binary distribution produced platform-tagged wheels
    # (…-cp311-cp311-linux_x86_64.whl) that cannot be reused across platforms.
    # CI asserts the wheel stays py3-none-any.
)
