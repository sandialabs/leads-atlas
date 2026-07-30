from leads_atlas.api import ExoiiDataset, transforms
from torch.utils.data import DataLoader


def main():
    transform = transforms.SampleMultiBlock(
        resolution=(1000, 500),
    )
    dataset = ExoiiDataset(
        filepath="examples/data/fields.exo",
        transform=transform,
    )
    dataloader = DataLoader(
        dataset,
        batch_size=32,
        shuffle=True,
    )

    # Iterate through batches
    for batch_idx, data in enumerate(dataloader):
        print(f"Batch {batch_idx}: data = {data}")

        # Your training/inference code here
        # model(data)
        # ...
        # Note that `data` has values shaped as (batch_size, *original_data_shape)

    print("Done!")


if __name__ == "__main__":
    main()
