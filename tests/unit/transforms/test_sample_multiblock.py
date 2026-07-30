from pathlib import Path
from leads_atlas.transforms.sample_multiblock import SampleMultiBlock
from leads_atlas.datasets.exoii import ExoiiDataset
import pyvista as pv

import pytest


@pytest.fixture()
def mesh_source() -> Path:
    data_dir = Path(__file__).parent.parent.parent.parent / "examples" / "data"
    return data_dir / "fields.exo"


@pytest.fixture()
def multiblock(mesh_source: Path) -> pv.MultiBlock:
    dataset = ExoiiDataset(filepath=mesh_source, transform=None)
    multiblock = dataset[0]["data"]
    return multiblock


def test_output_is_dict(multiblock: pv.MultiBlock):
    resolution = (100, 100, 1)
    transform = SampleMultiBlock(resolution=resolution)
    output = transform(multiblock)
    assert isinstance(output, dict)
    print(output.keys())


def test_keys_match_expected(multiblock: pv.MultiBlock):
    resolution = (100, 100, 1)
    transform = SampleMultiBlock(resolution=resolution)
    output = transform(multiblock)
    assert set(output.keys()) == set(
        [
            "B_Field",
            "E_Field",
            "LOAD_BAL",
            "PROC_ID",
            "ObjectId",
            "vtkValidPointMask",
            "vtkGhostType",
        ]
    )


def test_arbitrary_structure(multiblock: pv.MultiBlock):
    resolution = (100, 100, 1)
    transform = SampleMultiBlock(resolution=resolution)
    inpt = {
        "foo": [1, 2, 3],
        "bar": multiblock,
    }
    output = transform(inpt)
    assert output["foo"] == inpt["foo"]
    assert isinstance(output["bar"], dict)
