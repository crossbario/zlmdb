.PHONY: clean clean-docs clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test clean-docs ## remove all build, test, coverage, Python artifacts and docs

clean-docs:
	rm -fr docs/_build

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -f .coverage.*
	rm -fr htmlcov/
	rm -fr .pytest_cache
	-rm -rf .test*
	-rm -rf .mypy_cache

lint: ## check style with flake8
	flake8 zlmdb tests

test-single:
	clear && pytest -v -s zlmdb/tests/test_basic.py

test-quick:
	pytest

test:
	tox -e py36,flake8,coverage,mypy,yapf,sphinx

test-all:
	tox

coverage: ## check code coverage quickly with the default Python
	#coverage run --source zlmdb -m pytest
	coverage run --source zlmdb --omit="zlmdb/flatbuffer/reflection/*,zlmdb/flatbuffer/demo/*,zlmdb/tests/*" -m pytest -v -s zlmdb
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

docs: ## generate Sphinx HTML documentation, including API docs
	sphinx-build -b html ./docs ./docs/_build
	$(BROWSER) docs/_build/index.html

dist: clean ## builds source and wheel package
	python setup.py sdist bdist_wheel
	ls -la dist
	unzip -l dist/zlmdb-*-py2.py3-none-any.whl

# publish to PyPI
publish: dist
	twine upload dist/*

install:
	pip install -e .
	pip install -r requirements-dev.txt

# auto-format code - WARNING: this my change files, in-place!
autoformat:
	yapf -ri --style=yapf.ini --exclude="zlmdb/flatbuffers/*" zlmdb

update_flatbuffers:
	git submodule foreach git pull
	rm -rf ./flatbuffers
	cp -R deps/flatbuffers/python/flatbuffers .

generate_flatbuffers:
	~/scm/3rdparty/flatbuffers/flatc --python -o zlmdb/flatbuffers/ zlmdb/flatbuffers/demo1.fbs
	~/scm/3rdparty/flatbuffers/flatc --python -o zlmdb/flatbuffers/ zlmdb/flatbuffers/demo2.fbs
	~/scm/3rdparty/flatbuffers/flatc --python -o zlmdb/flatbuffers/ deps/flatbuffers/reflection/reflection.fbs

# input .fbs files for schema
FBS_FILES=deps/flatbuffers/reflection/reflection.fbs
FBS_OUTPUT=./crossbarfx/master/database/

# flatc compiler to use (build directly from master: https://github.com/google/flatbuffers)
# oberstet@thinkpad-t430s:~$ which flatc
# /usr/local/bin/flatc
# oberstet@thinkpad-t430s:~$ flatc --version
# flatc version 1.9.0 (Jun 21 2018 14:06:19)
# oberstet@thinkpad-t430s:~$ flatc --help | grep builtin
#   --bfbs-builtins    Add builtin attributes to the binary schema files.
# oberstet@thinkpad-t430s:~$

FLATC=${HOME}/scm/3rdparty/flatbuffers/flatc
#FLATC=/usr/local/bin/flatc

flatc_version:
	$(FLATC) --version

build_fbs: build_fbs_bfbs build_fbs_python

# generate schema type library (.bfbs binary) from schema files
build_fbs_bfbs:
	$(FLATC) -o $(FBS_OUTPUT) --binary --schema --bfbs-comments --bfbs-builtins $(FBS_FILES)

# generate python bindings from schema files
build_fbs_python:
	$(FLATC) -o $(FBS_OUTPUT) --python $(FBS_FILES)


# deps/flatbuffers/flatc
# deps/flatbuffers/libflatbuffers.a
# deps/flatbuffers/include/
flatbuffers_library:
	cd deps/flatbuffers && cmake -DCMAKE_BUILD_TYPE=Release . && make && make test && cd ../..


# load_fbs(repo_oid, source_name, source_code) -> BFBS -> return UUID

# parser()
# parser.parse_from_fbs(source_name: str, source_code: str, include_dirs=[]: List[str])
# parser.serialize_to_bfbs -> bytes
# parser.conforms_to(other_parser)

# // Checks that the schema represented by this parser is a safe evolution
# // of the schema provided. Returns non-empty error on any problems.

# JSON parsing 	Yes 	No 	No 	No 	No 	No 	No 	Yes 	No 	No 	No
# Simple mutation 	Yes 	Yes 	Yes 	Yes 	No 	No 	No 	No 	No 	No 	No
# Reflection 	Yes 	No 	No 	No 	No 	No 	No 	Basic 	No 	No 	No
# Buffer verifier
