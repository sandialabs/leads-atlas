import torch
from torch.utils.data import Dataset


class TimepairDataset(Dataset):
    def __init__(self, source: Dataset, stride: int = 1):
        """Initializes the dataset for data in a Exodus II data format.

        Args:
            filepath (os.PathLike): Path to the `.exo` file.
            resolution (tuple[int, int]): Sample resolution of points (not cells) in (y, x)

        Returns:
            Self: The ExoiiDataset object.
        """
        if not isinstance(source, Dataset):
            raise TypeError(
                f"Argument `source` must be type `torch.utils.data.Dataset`, got type `{type(source)}`"
            )
        if len(source) < 1:
            raise ValueError(f"Argument `source` is empty [{len(source)=}]")
        if not isinstance(stride, int):
            raise TypeError(
                f"Argument `stride` must be type `int`, got type `{type(stride)}`"
            )
        if stride < 1:
            raise ValueError(f"Argument `stride` must be >= 1, got value `{stride=}")
        if stride >= len(source):
            raise ValueError(
                "Argument `stride` is greater than the length of the source dataset"
            )
        self.stride = stride
        self.source = source

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        """Returns the data at the corresponding index sampled at a grid.

        Args:
            index (int): Index of the data to retrieve
        """
        t0 = self.source[index]
        tf = self.source[index + self.stride]
        return dict(t0=t0, tf=tf)

    def __len__(self) -> int:
        """Returns the length of the dataset."""
        source_length = len(self.source)
        return source_length - self.stride
