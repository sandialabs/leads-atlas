import torch
import pyvista as pv
from torchvision.transforms.v2 import Transform
from typing import Any, TypeAlias, Callable

Transformable: TypeAlias = type | Callable[[Any], bool]


class SampleMultiBlock(Transform):
    _transformed_types: tuple[Transformable, ...] = (pv.MultiBlock,)

    def __init__(self, resolution: tuple[int, ...]):
        """Initializes a transform for sampling cell data from a pyvista.MultiBlock into a rectangular grid.

        Args:
            resolution (tuple[int, ...]): Resolution of the grid to sample.
        """
        super().__init__()
        validate_resolution(resolution=resolution)
        if len(resolution) == 2:
            resolution = (*resolution, 1)
        self.resolution = resolution

    def transform(self, inpt: Any, params: dict[str, Any]):
        """Transforms an input from a torch Dataset.

        Args:
            inpt (Any): Data to be transformed
            params (dict[str, Any]): Unused.
        """
        if isinstance(inpt, pv.MultiBlock):
            return multiblock_to_tensors(multiblock=inpt, resolution=self.resolution)
        else:
            return inpt


def validate_resolution(resolution: tuple[int, ...]):
    """Validates the resolution parameter from user is correct."""
    if not isinstance(resolution, tuple):
        raise TypeError(
            f"Argument `resolution` expected a tuple, got f{type(resolution)=}"
        )
    if not all(isinstance(x, int) for x in resolution):
        types = tuple(type(x) for x in resolution)
        raise TypeError(
            f"Argument `resolution` expected tuple of integers, got {types=}"
        )
    if len(resolution) not in [2, 3]:
        raise ValueError(
            f"Argument `resolution` expected a tuple of length 2 or 3, got {len(resolution)=}"
        )


def multiblock_to_tensors(
    multiblock: pv.MultiBlock, resolution: tuple[int, int, int]
) -> dict[str, torch.Tensor]:
    """Combines and samples a multiblock at a given resolution and returns them as tensors.

    Args:
        multiblock (pv.MultiBlock): The data from the .exo file
        resolution (tuple[int, int, int]): The amount of points (not cells) to sample, in (x,y,z) format

    Returns:
        dict[str, torch.Tensor]: Tensors for each field in the cell data
    """
    mesh: pv.UnstructuredGrid = multiblock.flatten().combine()
    xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds
    ny, nx, nz = resolution
    dimensions = (nx, ny, nz)
    origin = (xmin, ymin, zmin)
    spacing = (
        (xmax - xmin) / nx,
        (ymax - ymin) / ny,
        (zmax - zmin) / nz,
    )
    grid = pv.ImageData(dimensions=dimensions, origin=origin, spacing=spacing)
    samples = grid.sample(mesh)
    tensors = {
        k: torch.Tensor(samples.point_data[k]).reshape(ny, nx, -1)
        for k in samples.point_data.keys()
    }
    return tensors
