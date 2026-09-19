"""Minimal Hugging Face Transformers training step tracked by EcoTraceCallback.

Requires the optional ML dependencies: pip install ecotrace[ml] transformers
"""

from ecotrace.callbacks.huggingface import EcoTraceCallback

from transformers import Trainer, TrainingArguments


def main() -> None:
    callback = EcoTraceCallback(
        model_name="demo-model",
        output_dir="./emissions",
        verbose=True,
    )

    training_args = TrainingArguments(
        output_dir="./demo-out",
        num_train_epochs=1,
        report_to=[],
    )

    trainer = Trainer(
        model=None,  # replace with your model
        args=training_args,
        callbacks=[callback],
    )

    # trainer.train() emits per-epoch emission records through the callback
    print(f"tracked emissions so far: {callback.total_emissions_kg} kg")


if __name__ == "__main__":
    main()
