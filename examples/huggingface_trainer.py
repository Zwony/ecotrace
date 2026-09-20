"""
Minimal Hugging Face Trainer example with EcoTrace.

Requires: torch, transformers
"""

import torch
from torch.utils.data import Dataset
from transformers import (
    BertConfig,
    BertForSequenceClassification,
    Trainer,
    TrainingArguments,
)

from ecotrace.callbacks import EcoTraceCallback


class TinyDataset(Dataset):
    """Small synthetic dataset for a local Trainer example."""

    def __init__(self, size: int = 8) -> None:
        self.input_ids = torch.randint(0, 32, (size, 8))
        self.attention_mask = torch.ones((size, 8), dtype=torch.long)
        self.labels = torch.randint(0, 2, (size,))

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        return {
            "input_ids": self.input_ids[index],
            "attention_mask": self.attention_mask[index],
            "labels": self.labels[index],
        }


def main() -> None:
    """Train a tiny model while EcoTrace tracks emissions."""
    config = BertConfig(
        vocab_size=32,
        hidden_size=16,
        num_hidden_layers=1,
        num_attention_heads=2,
        intermediate_size=32,
        num_labels=2,
    )

    model = BertForSequenceClassification(config)
    dataset = TinyDataset()

    training_args = TrainingArguments(
        output_dir="examples/huggingface_output",
        num_train_epochs=1,
        per_device_train_batch_size=2,
        logging_steps=1,
        report_to=[],
        disable_tqdm=True,
    )

    callback = EcoTraceCallback(
        project_name="huggingface-trainer-example",
        verbose=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        callbacks=[callback],
    )

    trainer.train()

    print(f"Emissions: {callback.total_emissions_kg:.8f} kg CO2")


if __name__ == "__main__":
    main()
