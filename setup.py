#-*-coding:utf-8-*-
"""
@FileName:
    setup.py
@Description:
    setup for mnsim noc
@CreateTime:
    2021/10/08 16:42
"""
import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

HERE = os.path.dirname(os.path.abspath((__file__)))

# meta info for repo
NAME = "MNSIM_NoC"
with open(os.path.join(HERE, "mnsim_noc", "VERSION")) as f:
    VERSION = f.read().strip()
LICENCE = "MIT"
URL = "https://github.com/ILTShade/MNSIM_NoC"

DESCRIPTION = "Dynamic Network no Chip implementation"
with open(os.path.join(HERE, "README.md")) as f:
    LONG_DESCRIPTION = "\n".join(f.readlines())

AUTHORS = "Hanbo Sun, Zhenhua Zhu, Tongxin Xie"
EMAIL = "sunhanbo123@163.com"

# packages for install
PACKAGES = find_packages(exclude=["tests.*", "tests"])
PY_MODULES = []

with open(os.path.join(HERE, "requirements.txt")) as f:
    INSTALL_REQUIRES = [v.strip() for v in f.readlines()]
EXTRAS_REQUIRE = dict()
TESTS_REQUIRE = [
    "pytest",
    "pytest-cov",
]

# extra pytest
class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ["tests/", "-x", "--cov"]
        self.test_suite = True

    def run_tests(self):
        import pytest
        error = pytest.main(self.test_args)
        sys.exit(error)

setup(
    name=NAME,
    version=VERSION,
    license=LICENCE,
    url=URL,

    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,

    author=AUTHORS,
    author_email=EMAIL,

    py_modules=PY_MODULES,
    packages=PACKAGES,

    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    tests_require=TESTS_REQUIRE,

    entry_points={
        "console_scripts": [
            "mnsim_noc=mnsim_noc.main:main",
        ]
    },

    cmdclass={"test": PyTest},

    zip_safe=True,
)
