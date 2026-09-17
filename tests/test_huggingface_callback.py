import os

from ecotrace.callbacks import (
    EcoTraceCallback,
    EcoTraceHuggingFaceCallback,
    EcoTraceTrainerCallback,
)


def test_callback_import_aliases():
    assert EcoTraceCallback is EcoTraceTrainerCallback
    assert EcoTraceCallback is EcoTraceHuggingFaceCallback


def test_callback_lifecycle_and_csv_logging():
    csv_path = "ecotrace_log.csv"
    initial_size = os.path.getsize(csv_path) if os.path.isfile(csv_path) else 0

    cb = EcoTraceCallback(model_name="test_bert_model", verbose=False)
    cb.on_train_begin()

    class DummyState:
        epoch = 1

    cb.on_epoch_begin()
    _ = [x * x for x in range(50000)]
    cb.on_epoch_end(state=DummyState())

    logs = {"loss": 0.45, "learning_rate": 2e-5}
    cb.on_log(logs=logs)
    assert "carbon_gco2" in logs
    assert "emissions_kg" in logs
    assert logs["carbon_gco2"] >= 0.0

    cb.on_train_end()

    assert not cb._is_training
    assert cb.total_emissions_kg >= 0.0
    assert cb.total_emissions_g >= 0.0
    assert len(cb._epoch_records) == 1
    assert cb._epoch_records[0]["epoch"] == 1

    assert os.path.isfile(csv_path)
    assert os.path.getsize(csv_path) > initial_size


def test_callback_custom_output_file(tmp_path):
    out_dir = str(tmp_path)
    out_file = "hf_emissions.csv"

    cb = EcoTraceCallback(
        model_name="test_gpt_model",
        output_dir=out_dir,
        output_file=out_file,
        verbose=False,
    )
    cb.on_train_begin()
    _ = sum(range(10000))
    cb.on_train_end()

    full_path = os.path.join(out_dir, out_file)
    assert os.path.isfile(full_path)
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "test_gpt_model" in content
