import os
from pathlib import Path
from typing import Callable, Any
import pyvista as pv
from torch.utils.data import Dataset

from leads_atlas.errors import VistaloaderError
from leads_atlas.datasets.common import DatasetItem


class PvdDataset(Dataset):
    def __init__(
        self,
        filepath: os.PathLike,
        transform: Callable[[pv.MultiBlock], Any] | None = None,
    ):
        """Initializes the dataset for data in a PVD data format.

        Args:
            filepath (os.PathLike): Path to the `.pvd` file.
            transform (Callable | None): Transform to apply to the dataset

        Returns:
            Self: The ExoiiDataset object.
        """
        self.transform = transform
        self.path = Path(filepath)
        if not (self.path.is_file() and self.path.suffix in [".pvd"]):
            raise VistaloaderError(
                f"Dataset is not a `pvd` file: {self.path.as_posix()}"
            )
        self.reader: pv.PVDReader = pv.get_reader(self.path)

    def __getitem__(self, index: int) -> pv.MultiBlock | Any:
        """Returns the data at the corresponding index sampled at a grid.

        Args:
            index (int): Index of the data to retrieve
        """
        if index < 0 or index >= len(self):
            raise IndexError(
                f"Index {index} out of range for `ExoiiDataset` of length {len(self)}"
            )

        self.reader.set_active_time_point(index)
        multiblock: pv.MultiBlock = self.reader.read()
        if self.transform is not None:
            multiblock = self.transform(multiblock)
        output = DatasetItem(data=multiblock, metadata=dict())
        return output

    def __len__(self) -> int:
        """Returns the length of the dataset."""
        return self.reader.number_time_points
