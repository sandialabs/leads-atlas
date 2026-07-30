from leads_atlas.api import ExoiiDataset, TimepairDataset, transforms
from leads_atlas.s3 import S3File as S3File
from torch.utils.data import DataLoader
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Subset


class ToyModel(nn.Module):
    """Single linear layer"""

    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(10000, 10000)  # 100*100*1 = 10000

    def forward(self, x):
        batch_size = x.shape[0]
        x_flat = x.reshape(batch_size, -1)
        out = self.fc(x_flat)
        return out.reshape(batch_size, 100, 100, 1)


def get_dataloader(filepath: str) -> DataLoader:
    source_dataset = ExoiiDataset(
        filepath=filepath,
        transform=transforms.SampleMultiBlock(resolution=(100, 100)),
    )
    dataset = TimepairDataset(
        source=source_dataset,
        # Here, we keep our stride at 1 as our dataset is only a couple of steps
        # For a larger dataset, this could be changed!
        stride=1,
    )
    # For a larger dataset, you can increase this significantly
    # The dataset and this value is kept small so the example runs fast
    NUM_DATAPOINTS = 2
    truncated = Subset(dataset, range(NUM_DATAPOINTS))
    return DataLoader(
        dataset=truncated,
        batch_size=1,
        shuffle=True,
    )


def initialize_model():
    model = ToyModel()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    return model, criterion, optimizer


def train_batch(x, y, model, criterion, optimizer) -> float:
    # Forward pass
    pred = model(x)
    loss = criterion(pred, y)

    # Backward pass
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    return loss.item()


def main():
    NUM_EPOCHS = 3
    # To mess with a larger dataset, try swapping this out to fields-big.exo
    with S3File("s3://exo/fields.exo", use_cache=True) as filepath:
        model, criterion, optimizer = initialize_model()
        dataloader = get_dataloader(filepath=filepath)

        print(f"Training for {NUM_EPOCHS} epochs.")
        for epoch in range(NUM_EPOCHS):
            epoch_loss = 0.0
            for batch_idx, batch in enumerate(dataloader):
                # Extract t0 and tf B_Field data
                x = batch["t0"]["data"]["B_Field"]
                y = batch["tf"]["data"]["B_Field"]
                batch_loss = train_batch(x, y, model, criterion, optimizer)
                epoch_loss += batch_loss
                print(
                    f"Epoch {epoch + 1}, Batch {batch_idx}, Batch Loss: {batch_loss:.8f}"
                )
            avg_loss = epoch_loss / len(dataloader)
            print(f"Epoch {epoch + 1} completed - Average Loss: {avg_loss:.8f}")
        print("Done!")


if __name__ == "__main__":
    main()
