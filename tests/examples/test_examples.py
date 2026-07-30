"""Run each example as a smoke-test to see if we broke user documentation."""

import pytest
import runpy
from pathlib import Path

# Ignore UserWarnings and DeprecationWarnings when running
# example files
pytestmark = [
    pytest.mark.filterwarnings("ignore::UserWarning"),
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
]


def discover_examples():
    root = Path(__file__).resolve().parents[2]
    matches = sorted((root / "examples").glob("[0-9]*-*.py"))
    return dict(
        argvalues=[str(match) for match in matches],
        ids=[match.name for match in matches],
    )


@pytest.mark.parametrize("example_file", **discover_examples())
def test_example(example_file, monkeypatch):
    # ensure non-interactive matplotlib
    monkeypatch.setenv("MPLBACKEND", "Agg")
    runpy.run_path(example_file, run_name="__main__")
