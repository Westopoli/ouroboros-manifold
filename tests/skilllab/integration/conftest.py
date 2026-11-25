# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md, piece LI1 (the version runner)
"""Fixtures for the LI1 tests (test_isolation_runner_*.py): one scratch root per pytest worker, so a version is built once per worker."""
import pytest


@pytest.fixture(scope="session")
def iso_scratch(tmp_path_factory):
    """The runner's scratch root: version trees and fight files go here and nowhere else. Pytest is started with --basetemp under engine-rules-baseline/li1/."""
    return tmp_path_factory.mktemp("iso-scratch")
