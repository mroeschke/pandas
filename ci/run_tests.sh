#!/bin/bash -e

# Workaround for pytest-xdist (it collects different tests in the workers if PYTHONHASHSEED is not set)
# https://github.com/pytest-dev/pytest/issues/920
# https://github.com/pytest-dev/pytest/issues/1075
export PYTHONHASHSEED=$(python -c 'import random; print(random.randint(1, 4294967295))')

# May help reproduce flaky CI builds if set in subsequent runs
echo PYTHONHASHSEED=$PYTHONHASHSEED

if [[ "not network" == *"$PATTERN"* ]]; then
    export http_proxy=http://1.2.3.4 https_proxy=http://1.2.3.4;
fi

COVERAGE="-s --cov=pandas --cov-report=xml --cov-append --cov-config=pyproject.toml"

# If no X server is found, we use xvfb to emulate it
if [[ $(uname) == "Linux" && -z $DISPLAY ]]; then
    export DISPLAY=":0"
    XVFB="xvfb-run "
fi

PYTEST_CMD="MESONPY_EDITABLE_VERBOSE=1 ${XVFB}pytest -v --setup-show -r fEs -n $PYTEST_WORKERS --dist=loadfile $TEST_ARGS $COVERAGE pandas/tests/api/ pandas/tests/apply/ pandas/tests/arithmetic/ pandas/tests/arrays/ pandas/tests/base/ pandas/tests/computation/ pandas/tests/config pandas/tests/construction pandas/tests/copy_view pandas/tests/dtypes pandas/tests/extension pandas/tests/frame pandas/tests/generic pandas/tests/groupby pandas/tests/indexes pandas/tests/indexing pandas/tests/interchange pandas/tests/internals pandas/tests/io pandas/tests/libs pandas/tests/plotting"

if [[ "$PATTERN" ]]; then
  PYTEST_CMD="$PYTEST_CMD -m \"$PATTERN\""
fi

echo $PYTEST_CMD
sh -c "$PYTEST_CMD"
