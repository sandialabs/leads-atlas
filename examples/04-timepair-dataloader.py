from leads_atlas.api import ExoiiDataset, TimepairDataset, transforms
from torch.utils.data import DataLoader


def main():
    transform = transforms.SampleMultiBlock(
        resolution=(100, 200),
    )
    source_dataset = ExoiiDataset(
        filepath="examples/data/fields.exo",
        transform=transform,
    )
    # Creates a dataset of with data in the form
    dataset = TimepairDataset(source=source_dataset, stride=1)
    dataloader = DataLoader(
        dataset=dataset,
        batch_size=32,
        shuffle=True,
    )

    # Iterate through batches
    for batch_idx, data in enumerate(dataloader):
        print(f"Batch {batch_idx}: data = {data}")

        # Your training/inference code here
        # model(data)
        # ...
        # Note that `data` is a dict with keys 't0' and 'tf'
        # The keys inside that dictionary are shaped as (batch_size, *original_data_shape)

    print("Done!")


if __name__ == "__main__":
    main()
