# Copyright 2026 Ubuntu
# See LICENSE file for licensing details.
#
# The integration tests use the Jubilant library. See https://documentation.ubuntu.com/jubilant/
# To learn more about testing, see https://documentation.ubuntu.com/ops/latest/explanation/testing/

import contextlib
import logging
import os
import pathlib
import sys
import time

import jubilant
import pytest

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption(
        "--keep-models",
        action="store_true",
        default=False,
        help="keep temporarily-created models",
    )
    parser.addoption("--model", default=None, help="Juju model to use for tests")


@pytest.fixture(scope="module")
def juju(request: pytest.FixtureRequest):
    """Create a temporary or use an existing Juju model for running tests."""
    keep_models = bool(request.config.getoption("--keep-models"))
    juju_model = request.config.getoption("--model")

    if juju_model:
        model_context = contextlib.nullcontext(jubilant.Juju(model=juju_model))
    else:
        model_context = jubilant.temp_model(keep=keep_models)

    with model_context as juju:
        yield juju

        if request.session.testsfailed:
            logger.info("Collecting Juju logs...")
            time.sleep(0.5)  # Wait for Juju to process logs.
            log = juju.debug_log(limit=1000)
            print(log, end="", file=sys.stderr)


@pytest.fixture(scope="session")
def charm():
    """Return the path of the charm under test."""
    if "CHARM_PATH" in os.environ:
        charm_path = pathlib.Path(os.environ["CHARM_PATH"])
        if not charm_path.exists():
            raise FileNotFoundError(f"Charm does not exist: {charm_path}")
        return charm_path
    # Modify below if you're building for multiple bases or architectures.
    charm_paths = list(pathlib.Path(".").glob("*.charm"))
    if not charm_paths:
        raise FileNotFoundError("No .charm file in current directory")
    if len(charm_paths) > 1:
        path_list = ", ".join(str(path) for path in charm_paths)
        raise ValueError(f"More than one .charm file in current directory: {path_list}")
    return charm_paths[0]
