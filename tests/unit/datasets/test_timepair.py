from pathlib import Path
import pytest
from leads_atlas.datasets.timepair import TimepairDataset
from leads_atlas.datasets.exoii import ExoiiDataset
import torch


def deep_equals(a, b):
    """
    Deep equality comparison that handles tensors, dicts, lists, and other types.

    Args:
        a: First object to compare
        b: Second object to compare

    Returns:
        bool: True if objects are deeply equal, False otherwise
    """
    # Check if types match
    if not isinstance(a, type(b)):
        return False

    # Handle torch tensors
    if isinstance(a, torch.Tensor):
        return torch.equal(a, b)

    # Handle dicts
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return False
        return all(deep_equals(a[key], b[key]) for key in a.keys())

    # Handle lists and tuples
    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(deep_equals(item_a, item_b) for item_a, item_b in zip(a, b))

    # Handle sets
    if isinstance(a, set):
        return a == b

    # For everything else, use standard equality
    return a == b


@pytest.fixture()
def source() -> ExoiiDataset:
    filepath = (
        Path(__file__).parent.parent.parent.parent / "examples" / "data" / "fields.exo"
    )
    source = ExoiiDataset(filepath=filepath)
    return source


# __init__ validation tests


def test_init_source_not_dataset_fails():
    """Test that init raises error when source is not a torch.utils.data.Dataset."""
    with pytest.raises(TypeError, match="Argument `source` must be type"):
        TimepairDataset(source=1, stride=1)


def test_init_stride_not_int_fails(source: ExoiiDataset):
    """Test that init raises error when stride is not an int."""
    with pytest.raises(TypeError, match="Argument `stride` must be type"):
        TimepairDataset(source=source, stride=source)


def test_init_stride_less_than_one_fails(source: ExoiiDataset):
    """Test that init raises error when stride < 1."""
    with pytest.raises(ValueError, match="Argument `stride` must be >= 1"):
        TimepairDataset(source=source, stride=0)


def test_init_stride_equals_source_length_fails(source: ExoiiDataset):
    """Test that init raises error when stride >= len(source)."""
    with pytest.raises(ValueError, match="Argument `stride` is greater than"):
        TimepairDataset(source=source, stride=3)


def test_init_source_empty_fails(source: ExoiiDataset):
    """Test that init raises error when source dataset is empty."""

    class EmptyDataset(torch.utils.data.Dataset):
        def __init__(self): ...

        def __getitem__(self, index): ...

        def __len__(self):
            return 0

    source = EmptyDataset()
    with pytest.raises(ValueError, match="Argument `source` is empty"):
        TimepairDataset(source=source, stride=1)


def test_init_valid(source: ExoiiDataset):
    """Test that init succeeds with valid source and stride."""
    TimepairDataset(source=source, stride=1)


# __len__ tests


@pytest.mark.parametrize("stride", [1, 2])
def test_len_returns_correct_value(source: ExoiiDataset, stride: int):
    """Test that __len__ returns len(source) - stride."""
    gt = 3 - stride
    dataset = TimepairDataset(source=source, stride=stride)
    assert len(dataset) == gt


# __getitem__ tests


def test_getitem_returns_dict(source: ExoiiDataset):
    """Test that __getitem__ returns a dict."""
    dataset = TimepairDataset(source=source)
    assert isinstance(dataset[0], dict)


def test_getitem_has_t0_and_tf_keys(source: ExoiiDataset):
    """Test that __getitem__ returns dict with 't0' and 'tf' keys."""
    dataset = TimepairDataset(source=source)
    set(dataset[0].keys()) == {"t0", "tf"}


def test_getitem_t0_equals_source_at_index(source: ExoiiDataset):
    """Test that t0 equals source[index]."""
    dataset = TimepairDataset(source=source)
    assert deep_equals(dataset[0]["t0"], source[0])
    assert deep_equals(dataset[1]["t0"], source[1])


def test_getitem_tf_equals_source_at_index_plus_stride(source: ExoiiDataset):
    """Test that tf equals source[index + stride]."""
    stride = 1
    dataset = TimepairDataset(source=source, stride=stride)
    assert deep_equals(dataset[0]["tf"], source[0 + stride])
    assert deep_equals(dataset[1]["tf"], source[1 + stride])


def test_getitem_index_negative_fails(source: ExoiiDataset):
    """Test that __getitem__ raises error when index < 0."""
    dataset = TimepairDataset(source=source)
    with pytest.raises(IndexError):
        dataset[-1]


def test_getitem_index_at_length_fails(source: ExoiiDataset):
    """Test that __getitem__ raises error when index = len(TimepairDataset)."""
    dataset = TimepairDataset(source=source)
    with pytest.raises(IndexError):
        dataset[len(dataset)]


def test_getitem_index_above_length_fails(source: ExoiiDataset):
    """Test that __getitem__ raises error when index > len(TimepairDataset)."""
    dataset = TimepairDataset(source=source)
    with pytest.raises(IndexError):
        dataset[len(dataset) + 1]


def test_getitem_first_valid_index(source: ExoiiDataset):
    """Test that __getitem__ works correctly at index 0."""
    dataset = TimepairDataset(source=source)
    assert dataset[0] is not None


def test_getitem_last_valid_index(source: ExoiiDataset):
    """Test that __getitem__ works correctly at last valid index (len(source) - stride - 1)."""
    dataset = TimepairDataset(source=source)
    assert dataset[len(dataset) - dataset.stride - 1] is not None
