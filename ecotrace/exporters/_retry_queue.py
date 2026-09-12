"""Disk-backed retry queue for CloudExporter telemetry payloads.

Designed for low-memory environments (e.g., VPS with <=2 GB RAM). Payloads
are serialized to individual JSON files in a dedicated directory using atomic
write-then-rename patterns.
"""
from __future__ import annotations

import glob
import json
import os
import time
import uuid
from typing import Any

from ..logger import logger

DEFAULT_RETRY_DIR = os.path.expanduser("~/.ecotrace/retry_queue")
MAX_QUEUE_ENTRIES = 50


class RetryQueue:
    """Bounded, disk-backed FIFO queue for transient network telemetry failures.

    Attributes:
        queue_dir (str): Absolute directory path housing pending payload JSONs.
        max_size (int): Maximum allowable backlog files before dropping oldest entries.
    """

    def __init__(self, retry_dir: str | None = None, max_size: int = MAX_QUEUE_ENTRIES):
        env_dir = os.environ.get("ECOTRACE_RETRY_DIR")
        self.queue_dir = os.path.abspath(retry_dir or env_dir or DEFAULT_RETRY_DIR)
        self.max_size = max(1, int(max_size))
        os.makedirs(self.queue_dir, exist_ok=True)

    def push(self, payload: dict[str, Any]) -> str | None:
        """Atomically serializes payload to disk as a pending retry record.

        Args:
            payload: JSON-serializable telemetry dictionary.

        Returns:
            str: Path to the written file, or None if write failed.
        """
        temp_path: str | None = None
        try:
            now_ns = time.time_ns()
            uid = uuid.uuid4().hex[:8]
            target_filename = f"{now_ns}_{uid}.json"
            target_path = os.path.join(self.queue_dir, target_filename)
            temp_path = os.path.join(self.queue_dir, f".{target_filename}.tmp")

            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            os.replace(temp_path, target_path)
            self._prune_if_exceeded()
            return target_path
        except (OSError, TypeError, ValueError) as e:
            logger.debug(f"RetryQueue push failed: {e}")
            if temp_path is not None and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            return None

    def peek_oldest(self) -> tuple[str, dict[str, Any]] | None:
        """Retrieves the oldest queued payload without deleting it from disk.

        Returns:
            tuple: (file_path, payload_dict), or None if queue is empty.
        """
        files = self._get_sorted_queue_files()
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                return file_path, payload
            except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.debug(f"RetryQueue peek error for {file_path}: {e}")
                # Corrupt or unreadable file - remove to avoid infinite stall
                try:
                    os.remove(file_path)
                except OSError:
                    pass
        return None

    def delete(self, file_path: str) -> bool:
        """Removes a successfully dispatched payload from disk."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except OSError as e:
            logger.debug(f"RetryQueue delete failed for {file_path}: {e}")
        return False

    def clear(self) -> int:
        """Purges all files in the retry queue."""
        count = 0
        for file_path in self._get_sorted_queue_files():
            if self.delete(file_path):
                count += 1
        return count

    def _get_sorted_queue_files(self) -> list[str]:
        """Returns sorted list of pending JSON payload file paths (oldest first)."""
        pattern = os.path.join(self.queue_dir, "[0-9]*_*.json")
        try:
            files = glob.glob(pattern)
            files.sort()  # Timestamp prefix naturally sorts chronologically
            return files
        except OSError as e:
            logger.debug(f"RetryQueue listing failed: {e}")
            return []

    def _prune_if_exceeded(self):
        """Discards oldest entries if backlog exceeds max_size."""
        files = self._get_sorted_queue_files()
        if len(files) > self.max_size:
            excess_count = len(files) - self.max_size
            for f in files[:excess_count]:
                try:
                    os.remove(f)
                except OSError:
                    pass

    def __len__(self) -> int:
        return len(self._get_sorted_queue_files())
