import os
import time
import pytest
from unittest.mock import patch, MagicMock
from ecotrace.exporters._retry_queue import RetryQueue
from ecotrace.exporters.cloud import CloudExporter


def test_retry_queue_push_and_peek(tmp_path):
    """Verify push serializes payload to disk and peek retrieves it intact."""
    queue_dir = str(tmp_path / "queue")
    q = RetryQueue(retry_dir=queue_dir, max_size=10)

    payload = {"function": "test_fn", "carbon_gco2": 0.015, "duration_s": 1.2}
    path = q.push(payload)

    assert path is not None
    assert os.path.exists(path)
    assert len(q) == 1

    item = q.peek_oldest()
    assert item is not None
    file_path, retrieved = item
    assert file_path == path
    assert retrieved == payload


def test_retry_queue_fifo_order(tmp_path):
    """Verify queue strictly respects FIFO ordering across multiple items."""
    queue_dir = str(tmp_path / "queue")
    q = RetryQueue(retry_dir=queue_dir, max_size=10)

    p1 = {"item": 1}
    p2 = {"item": 2}
    p3 = {"item": 3}

    q.push(p1)
    time.sleep(0.002)
    q.push(p2)
    time.sleep(0.002)
    q.push(p3)

    assert len(q) == 3

    item1 = q.peek_oldest()
    assert item1 is not None
    path1, val1 = item1
    assert val1["item"] == 1
    q.delete(path1)

    item2 = q.peek_oldest()
    assert item2 is not None
    path2, val2 = item2
    assert val2["item"] == 2
    q.delete(path2)

    item3 = q.peek_oldest()
    assert item3 is not None
    path3, val3 = item3
    assert val3["item"] == 3
    q.delete(path3)

    assert len(q) == 0


def test_retry_queue_max_size_pruning(tmp_path):
    """Verify oldest items are pruned when max_size is reached."""
    queue_dir = str(tmp_path / "queue")
    q = RetryQueue(retry_dir=queue_dir, max_size=3)

    for i in range(5):
        q.push({"idx": i})
        time.sleep(0.002)

    assert len(q) == 3
    oldest_res = q.peek_oldest()
    assert oldest_res is not None
    _, oldest = oldest_res
    # Items 0 and 1 should have been discarded, oldest remaining should be item 2
    assert oldest["idx"] == 2


def test_retry_queue_corrupt_file_handling(tmp_path):
    """Verify corrupt JSON files are safely skipped and deleted on peek."""
    queue_dir = str(tmp_path / "queue")
    q = RetryQueue(retry_dir=queue_dir, max_size=10)

    # Create a corrupt file
    corrupt_path = os.path.join(queue_dir, "1000_bad.json")
    with open(corrupt_path, "w") as f:
        f.write("{invalid json content")

    # Push a valid file after it
    q.push({"valid": True})

    assert os.path.exists(corrupt_path)
    item = q.peek_oldest()
    assert item is not None
    _, payload = item
    assert payload == {"valid": True}
    # Corrupt file should have been deleted
    assert not os.path.exists(corrupt_path)


def test_cloud_exporter_success_no_buffering(tmp_path):
    """When endpoint returns 200, no file is persisted to the retry queue."""
    queue_dir = str(tmp_path / "queue")
    exporter = CloudExporter(
        api_key="eco_usr_test123",
        endpoint="https://example.com/api/metrics/ingest",
        retry_dir=queue_dir
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch.object(exporter.session, "post", return_value=mock_resp):
        exporter.export(carbon_emitted=0.05, func_name="fast_task", duration=0.1)

    assert len(exporter.queue) == 0
    exporter.close()


def test_cloud_exporter_buffers_on_http_failure(tmp_path):
    """When endpoint returns 500, payload is persisted to disk and worker starts."""
    queue_dir = str(tmp_path / "queue")
    exporter = CloudExporter(
        api_key="eco_usr_test123",
        endpoint="https://example.com/api/metrics/ingest",
        retry_dir=queue_dir
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    with patch.object(exporter.session, "post", return_value=mock_resp):
        exporter.export(carbon_emitted=0.12, func_name="failed_task", duration=0.5)

    assert len(exporter.queue) == 1
    res = exporter.queue.peek_oldest()
    assert res is not None
    file_path, item = res
    assert item["function"] == "failed_task"
    assert item["carbon_gco2"] == 0.12
    exporter.close()


def test_cloud_exporter_buffers_on_network_exception(tmp_path):
    """When network raises ConnectionError, payload is persisted to disk."""
    queue_dir = str(tmp_path / "queue")
    exporter = CloudExporter(
        api_key="eco_usr_test123",
        endpoint="https://example.com/api/metrics/ingest",
        retry_dir=queue_dir
    )

    with patch.object(exporter.session, "post", side_effect=ConnectionError("Host unreachable")):
        exporter.export(carbon_emitted=0.08, func_name="net_failed_task", duration=0.3)

    assert len(exporter.queue) == 1
    exporter.close()


def test_cloud_exporter_flush_drains_queue(tmp_path):
    """flush() synchronously drains all queued payloads when endpoint recovers."""
    queue_dir = str(tmp_path / "queue")
    exporter = CloudExporter(
        api_key="eco_usr_test123",
        endpoint="https://example.com/api/metrics/ingest",
        retry_dir=queue_dir
    )

    # Manually push 2 items to simulate offline backlog
    exporter.queue.push({"function": "task1", "carbon_gco2": 0.01})
    exporter.queue.push({"function": "task2", "carbon_gco2": 0.02})
    assert len(exporter.queue) == 2

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch.object(exporter.session, "post", return_value=mock_resp):
        drained = exporter.flush(timeout=2.0)
        assert drained is True
        assert len(exporter.queue) == 0

    exporter.close()
