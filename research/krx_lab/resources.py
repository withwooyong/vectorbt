"""Cooperative, same-host resource observation for synthetic experiment workers.

This module samples the current Python process and the filesystem containing an
experiment output directory.  It requests a stop at a later C4 checkpoint; it
does not configure OS resource limits, kill processes, or coordinate workers
on other hosts.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
import math
from pathlib import Path
import shutil
import threading
import time
from typing import Any

import psutil

from .contracts import CooperativeStop, ResourceSample


@dataclass(frozen=True)
class ResourceLimits:
    """Optional observation thresholds, expressed in bytes and seconds."""

    max_rss_bytes: int | None = None
    min_free_disk_bytes: int | None = None
    poll_interval_seconds: float = 1.0

    def __post_init__(self) -> None:
        for name in ("max_rss_bytes", "min_free_disk_bytes"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"INVALID_RESOURCE_LIMIT: {name}")
        if (isinstance(self.poll_interval_seconds, bool)
                or not isinstance(self.poll_interval_seconds, (int, float))
                or not math.isfinite(self.poll_interval_seconds)
                or self.poll_interval_seconds <= 0):
            raise ValueError("INVALID_RESOURCE_LIMIT: poll_interval_seconds")

    def asdict(self) -> dict[str, int | float | None]:
        """Return JSON-native limit values for persisted telemetry."""
        return asdict(self)

    @property
    def enabled(self) -> bool:
        return self.max_rss_bytes is not None or self.min_free_disk_bytes is not None


class ResourceMonitor:
    """Sample resources in a background thread and stop only at checkpoints.

    ``checkpoint`` has the ``ExecutionHooks`` callback signature.  A breached
    threshold or sampler fault is retained and raised as ``CooperativeStop``
    when that callback next runs.  The monitor intentionally makes no claim of
    an OS-enforced hard memory or disk limit.
    """

    def __init__(
        self,
        out: str | Path,
        limits: ResourceLimits,
        *,
        sampler: Callable[[], ResourceSample | tuple[int, int]] | None = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.out = Path(out)
        self.limits = limits
        self._sampler = sampler
        self._clock = clock
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._started_at: float | None = None
        self._last_sample: ResourceSample | None = None
        self._sample_count = 0
        self._sampled_peak_rss_bytes = 0
        self._reason: str | None = None
        self._sampler_error: str | None = None

    def __enter__(self) -> ResourceMonitor:
        if self._started_at is not None:
            raise RuntimeError("RESOURCE_MONITOR_ALREADY_STARTED")
        self._started_at = self._clock()
        if not self.limits.enabled:
            return self
        self._sample_once()
        if self._reason is None:
            self._thread = threading.Thread(target=self._run, name="krx-resource-monitor", daemon=True)
            self._thread.start()
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: Any) -> bool:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=max(1.0, min(5.0, self.limits.poll_interval_seconds + 1.0)))
        return False

    @property
    def sampled_peak_rss_bytes(self) -> int:
        with self._lock:
            return self._sampled_peak_rss_bytes

    @property
    def telemetry(self) -> dict[str, Any]:
        """Return bounded, JSON-native observation telemetry."""
        with self._lock:
            sample = self._last_sample
            return {
                "limits": self.limits.asdict(),
                "monitoring_enabled": self.limits.enabled,
                "sample_count": self._sample_count,
                "rss_bytes": sample.rss_bytes if sample else None,
                "peak_rss_bytes": self._sampled_peak_rss_bytes,
                "sampled_peak_rss_bytes": self._sampled_peak_rss_bytes,
                "disk_free_bytes": sample.disk_free_bytes if sample else None,
                "elapsed_seconds": sample.elapsed_seconds if sample else None,
                "reason": self._reason,
                "sampler_error": self._sampler_error,
            }

    def checkpoint(self, stage: str, context: Mapping[str, Any] | None = None) -> None:
        """C4 callback: raise the first observed cooperative stop reason."""
        del stage, context
        with self._lock:
            reason = self._reason
        if reason is not None:
            raise CooperativeStop(reason)

    def _run(self) -> None:
        while not self._stop_event.wait(self.limits.poll_interval_seconds):
            self._sample_once()
            with self._lock:
                if self._reason is not None:
                    return

    def _sample_once(self) -> None:
        try:
            raw_sample = self._sample() if self._sampler is None else self._sampler()
            rss_bytes, disk_free_bytes, supplied_peak = self._sample_values(raw_sample)
            assert self._started_at is not None
            elapsed_seconds = self._clock() - self._started_at
            with self._lock:
                peak_rss_bytes = max(self._sampled_peak_rss_bytes, rss_bytes, supplied_peak)
                self._sampled_peak_rss_bytes = peak_rss_bytes
                self._last_sample = ResourceSample(elapsed_seconds, rss_bytes, peak_rss_bytes, disk_free_bytes)
                self._sample_count += 1
                if self._reason is None and self.limits.max_rss_bytes is not None and peak_rss_bytes > self.limits.max_rss_bytes:
                    self._reason = "RSS_LIMIT"
                if self._reason is None and (self.limits.min_free_disk_bytes is not None
                                             and disk_free_bytes < self.limits.min_free_disk_bytes):
                    self._reason = "DISK_FREE_LIMIT"
        except Exception as exc:
            with self._lock:
                if self._reason is None:
                    self._reason = "MONITOR_FAILED"
                    self._sampler_error = f"{type(exc).__name__}: {exc}"

    def _sample(self) -> tuple[int, int]:
        return psutil.Process().memory_info().rss, shutil.disk_usage(self.out).free

    @staticmethod
    def _sample_values(sample: ResourceSample | tuple[int, int]) -> tuple[int, int, int]:
        if isinstance(sample, ResourceSample):
            return sample.rss_bytes, sample.disk_free_bytes, sample.peak_rss_bytes
        if (not isinstance(sample, tuple) or len(sample) != 2
                or type(sample[0]) is not int or type(sample[1]) is not int
                or sample[0] < 0 or sample[1] < 0):
            raise ValueError("INVALID_RESOURCE_SAMPLER_RESULT")
        return sample[0], sample[1], sample[0]
