import pytest
from leads_atlas.api import ExoiiDataset
from pathlib import Path


@pytest.fixture()
def mesh_source() -> Path:
    data_dir = Path(__file__).parent.parent.parent.parent / "examples" / "data"
    return data_dir / "fields.exo"


def test_dataset_len(mesh_source: Path):
    # A torch `Dataset` requires a __len__ implementation
    dataset = ExoiiDataset(filepath=mesh_source, transform=None)
    assert len(dataset) == 3


def test_dataset_getitem(mesh_source: Path):
    # A torch `Dataset` requires a __getitem__ implementation
    # Here we test that the data returned is what we expect
    dataset = ExoiiDataset(filepath=mesh_source, transform=None)
    # Pre-computed values we should be able to collect exactly,
    # assuming that we loaded the correct data.
    assert (
        dataset[0]["data"].flatten().combine()["B_Field"].mean().item()
        == -0.0189740753388411
    )
    assert (
        dataset[1]["data"].flatten().combine()["B_Field"].mean().item()
        == -0.019430371221735722
    )
    assert (
        dataset[2]["data"].flatten().combine()["B_Field"].mean().item()
        == -0.019887424611832474
    )


def test_fields_accessible(mesh_source: Path):
    # Test that we get the fields that we expect from the dataset
    dataset = ExoiiDataset(filepath=mesh_source, transform=None)
    for idx in range(len(dataset)):
        data = dataset[idx]["data"]
        assert set(data.keys()) == {
            "Edge Blocks",
            "Edge Sets",
            "Element Blocks",
            "Element Sets",
            "Face Blocks",
            "Face Sets",
            "Node Sets",
            "Side Sets",
        }


@pytest.mark.skip("Move to transforms test")
@pytest.mark.parametrize("resolution", [(64, 128), (50, 100), (32, 32)])
def test_resolution_matches(mesh_source: Path, resolution: tuple[int, int]):
    dataset = ExoiiDataset(filepath=mesh_source, transform=None)
    for key, value in dataset[0].items():
        assert value.shape[:2] == resolution, f"{key=}, {resolution=}, {value.shape=}"
