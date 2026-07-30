from leads_atlas.api import ExoiiDataset, TimepairDataset, transforms
from torch.utils.data import DataLoader
import torch.nn as nn
import torch.optim as optim


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


def main():
    source_dataset = ExoiiDataset(
        filepath="examples/data/fields.exo",
        transform=transforms.SampleMultiBlock(resolution=(100, 100)),
    )
    dataset = TimepairDataset(source=source_dataset, stride=1)
    dataloader = DataLoader(
        dataset=dataset,
        batch_size=1,
        shuffle=True,
    )

    # Initialize model
    model = ToyModel()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # Training loop
    num_epochs = 10
    for epoch in range(num_epochs):
        epoch_loss = 0.0
        for batch_idx, batch in enumerate(dataloader):
            # Extract t0 and tf B_Field data
            x = batch["t0"]["data"]["B_Field"]
            y = batch["tf"]["data"]["B_Field"]

            # Forward pass
            pred = model(x)
            loss = criterion(pred, y)

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

            print(
                f"Epoch {epoch + 1}/{num_epochs}, Batch {batch_idx}, Loss: {loss.item():.4f}"
            )

        avg_loss = epoch_loss / len(dataloader)
        print(f"Epoch {epoch + 1} completed - Average Loss: {avg_loss:.4f}")

    print("Done!")


if __name__ == "__main__":
    main()
