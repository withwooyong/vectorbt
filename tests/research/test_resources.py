from __future__ import annotations

import threading

import pytest

from research.krx_lab.contracts import CooperativeStop, ResourceSample
from research.krx_lab.resources import ResourceLimits, ResourceMonitor


def _sample(rss=100, disk=1_000, peak=None):
    return ResourceSample(0.0, rss, rss if peak is None else peak, disk)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_rss_bytes": -1},
        {"min_free_disk_bytes": -1},
        {"poll_interval_seconds": 0},
        {"poll_interval_seconds": float("inf")},
    ],
)
def test_resource_limits_fail_closed(kwargs):
    with pytest.raises(ValueError, match="INVALID_RESOURCE_LIMIT"):
        ResourceLimits(**kwargs)


def test_monitor_records_injected_peak_and_rss_limit(tmp_path):
    monitor = ResourceMonitor(tmp_path, ResourceLimits(max_rss_bytes=150), sampler=lambda: _sample(100, peak=200))
    with monitor:
        with pytest.raises(CooperativeStop, match="RSS_LIMIT"):
            monitor.checkpoint("simulation_day", {"run_id": "run-1"})
    assert monitor.sampled_peak_rss_bytes == 200
    assert monitor.telemetry == {
        "limits": {"max_rss_bytes": 150, "min_free_disk_bytes": None, "poll_interval_seconds": 1.0},
        "monitoring_enabled": True,
        "sample_count": 1,
        "rss_bytes": 100,
        "peak_rss_bytes": 200,
        "sampled_peak_rss_bytes": 200,
        "disk_free_bytes": 1_000,
        "elapsed_seconds": pytest.approx(0.0, abs=1.0),
        "reason": "RSS_LIMIT",
        "sampler_error": None,
    }


def test_monitor_disk_limit_and_sampler_failure_stop_at_checkpoint(tmp_path):
    disk_monitor = ResourceMonitor(
        tmp_path, ResourceLimits(min_free_disk_bytes=1_001), sampler=lambda: _sample(disk=1_000)
    )
    with disk_monitor:
        with pytest.raises(CooperativeStop, match="DISK_FREE_LIMIT"):
            disk_monitor.checkpoint("run_start")

    failed_monitor = ResourceMonitor(
        tmp_path, ResourceLimits(max_rss_bytes=10), sampler=lambda: (_ for _ in ()).throw(OSError("injected"))
    )
    with failed_monitor:
        with pytest.raises(CooperativeStop, match="MONITOR_FAILED"):
            failed_monitor.checkpoint("run_start")
    assert failed_monitor.telemetry["sampler_error"] == "OSError: injected"


def test_monitor_background_sampling_stops_on_context_exit(tmp_path):
    sampled_twice = threading.Event()
    calls = 0

    def sampler():
        nonlocal calls
        calls += 1
        if calls == 2:
            sampled_twice.set()
        return _sample(rss=100 + calls)

    monitor = ResourceMonitor(tmp_path, ResourceLimits(max_rss_bytes=10_000, poll_interval_seconds=0.01), sampler=sampler)
    with monitor:
        assert sampled_twice.wait(1)
        assert monitor._thread is not None
    assert monitor._thread is not None and not monitor._thread.is_alive()
    observed_calls = calls
    assert monitor.telemetry["sample_count"] == observed_calls


def test_monitor_preserves_context_exception(tmp_path):
    monitor = ResourceMonitor(tmp_path, ResourceLimits(max_rss_bytes=10_000), sampler=lambda: _sample())
    with pytest.raises(RuntimeError, match="caller fault"):
        with monitor:
            raise RuntimeError("caller fault")
    assert monitor._thread is not None and not monitor._thread.is_alive()


def test_unlimited_monitor_does_not_start_background_sampling(tmp_path):
    monitor = ResourceMonitor(tmp_path, ResourceLimits(), sampler=lambda: pytest.fail("sampler was called"))
    with monitor:
        monitor.checkpoint("run_start")
    assert monitor.telemetry["monitoring_enabled"] is False
    assert monitor.telemetry["sample_count"] == 0
