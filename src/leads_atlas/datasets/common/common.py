from typing import NamedTuple, Any
from collections.abc import KeysView, ValuesView, ItemsView


# This class *must* inheret from NamedTuple due to limitations
# from PyTorch's DataLoaders. The default collate function used
# by torch collates on a few specific types, one of which is
# hardcoded in their source-code to be for named tuples.
#
# If we did not do this, we would require everyone to use a
# custom dataloader we would write, or we would need to maintain
# a custom collate function, which is extra effort, error prone,
# and easy to forget.
class DatasetItem(NamedTuple):
    """An individual item from a LEADS Atlas dataset."""

    data: Any
    metadata: dict[str, Any]

    def __getitem__(self, key: str) -> Any:
        """x.__getitem__(y) <==> x[y]"""
        return self._asdict()[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for key if key is in the dictionary, else default."""
        return self._asdict().get(key=key, default=default)

    def items(self) -> ItemsView[str, Any]:
        """D.items() -> a set-like object providing a view on D's items."""
        return self._asdict().items()

    def keys(self) -> KeysView[str]:
        """D.keys() -> a set-like object providing a view on D's keys."""
        return self._asdict().keys()

    def values(self) -> ValuesView[Any]:
        """D.values() -> an object providing a view on D's values."""
        return self._asdict().values()
