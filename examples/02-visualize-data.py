# Example: 02-visualize-data.py
from pathlib import Path
import matplotlib.pyplot as plt
from torch import Tensor

from leads_atlas.api import ExoiiDataset, transforms


def minmax_normalize(tensor: Tensor):
    """Normalizes a tensor for visualization."""
    return (tensor - tensor.min()) / (tensor.max() - tensor.min())


def visualize(tensor: Tensor, title: str):
    """Normalize the tensor so RGB values don't clip and visualize"""
    # In a ML pipeline, we would normally let provided transforms
    # do this for us instead of writing it automatically and apply
    # while using the dataloader
    #
    # For the sake of keeping this example barebones, we omit using a
    # dataloader here.
    norm_tensor = minmax_normalize(tensor)

    # Create the visualization
    plt.figure(figsize=(12, 6))
    plt.imshow(norm_tensor, aspect="auto", origin="lower", cmap="viridis")
    plt.colorbar(label=f"{title} value")
    plt.xlabel("X index")
    plt.ylabel("Y index")
    plt.title(f"{title} field sampled at resolution {tensor.shape}")
    plt.show()


def main() -> None:
    dataset_path = Path(__file__).parent / "data" / "fields.exo"
    print(f"Loading dataset at {dataset_path}")
    transform = transforms.SampleMultiBlock(
        resolution=(1000, 500),
    )
    dataset = ExoiiDataset(filepath=dataset_path, transform=transform)

    print(f"Dataset loaded from {dataset_path}")
    print(f"Total timesteps: {len(dataset)}")

    print("Tensors at timesteps:")
    print(dataset[0].keys())
    visualize(dataset[0]["data"]["E_Field"], "E_Field@time=0")
    visualize(dataset[1]["data"]["E_Field"], "E_Field@time=1")
    visualize(dataset[2]["data"]["E_Field"], "E_Field@time=2")


if __name__ == "__main__":
    main()
