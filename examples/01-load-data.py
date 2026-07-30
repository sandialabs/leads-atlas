# Example: 01-load-data.py
from pathlib import Path

from leads_atlas.api import ExoiiDataset


def main() -> None:
    dataset_path = Path(__file__).parent / "data" / "fields.exo"
    print(f"Loading dataset at {dataset_path}")
    dataset = ExoiiDataset(filepath=dataset_path)

    print(f"Dataset loaded from {dataset_path}")
    print(f"Total timesteps: {len(dataset)}")


if __name__ == "__main__":
    main()
