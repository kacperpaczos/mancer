"""
Performance monitoring utilities for E2E tests.

This module provides tools for collecting performance metrics,
monitoring resource usage, and detecting performance regressions
during end-to-end test execution.
"""

import time
import psutil
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json


logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """Snapshot of system performance at a point in time."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage: Dict[str, float]
    network_io: Dict[str, int]
    container_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class PerformanceReport:
    """Comprehensive performance report for a test run."""
    test_name: str
    start_time: datetime
    end_time: datetime
    duration: float
    peak_memory_usage: float
    average_cpu_usage: float
    total_network_io: Dict[str, int]
    operation_timings: Dict[str, float]
    snapshots: List[PerformanceSnapshot] = field(default_factory=list)
    regressions_detected: List[str] = field(default_factory=list)


class PerformanceMonitor:
    """Monitors system performance during E2E tests."""

    def __init__(self, baseline_file: Optional[Path] = None):
        self.baseline_file = baseline_file or Path("performance_baseline.json")
        self.snapshots: List[PerformanceSnapshot] = []
        self.operation_timings: Dict[str, float] = {}
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.baseline_data: Optional[Dict[str, Any]] = None

        # Load baseline data if available
        self._load_baseline()

    def start_monitoring(self, test_name: str) -> None:
        """Start performance monitoring for a test."""
        self.test_name = test_name
        self.start_time = datetime.now()
        self.snapshots = []
        logger.info(f"Started performance monitoring for {test_name}")

    def stop_monitoring(self) -> PerformanceReport:
        """Stop monitoring and generate performance report."""
        self.end_time = datetime.now()

        if not self.start_time:
            raise RuntimeError("Monitoring not started")

        duration = (self.end_time - self.start_time).total_seconds()

        # Calculate aggregated metrics
        peak_memory = max((s.memory_percent for s in self.snapshots), default=0.0)
        avg_cpu = sum(s.cpu_percent for s in self.snapshots) / len(self.snapshots) if self.snapshots else 0.0

        # Calculate total network I/O
        total_network = {"bytes_sent": 0, "bytes_recv": 0}
        if self.snapshots:
            first = self.snapshots[0]
            last = self.snapshots[-1]
            total_network["bytes_sent"] = last.network_io["bytes_sent"] - first.network_io["bytes_sent"]
            total_network["bytes_recv"] = last.network_io["bytes_recv"] - first.network_io["bytes_recv"]

        # Check for regressions
        regressions = self._detect_regressions(duration, peak_memory, avg_cpu)

        report = PerformanceReport(
            test_name=self.test_name,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=duration,
            peak_memory_usage=peak_memory,
            average_cpu_usage=avg_cpu,
            total_network_io=total_network,
            operation_timings=self.operation_timings.copy(),
            snapshots=self.snapshots.copy(),
            regressions_detected=regressions
        )

        logger.info(f"Generated performance report for {self.test_name}")
        return report

    def take_snapshot(self, container_stats: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        """Take a performance snapshot."""
        timestamp = datetime.now()

        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Disk usage
        disk_usage = {}
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage[partition.mountpoint] = usage.percent
            except (PermissionError, OSError):
                continue

        # Network I/O
        network_io = psutil.net_io_counters()
        network_stats = {
            "bytes_sent": network_io.bytes_sent,
            "bytes_recv": network_io.bytes_recv,
            "packets_sent": network_io.packets_sent,
            "packets_recv": network_io.packets_recv
        }

        snapshot = PerformanceSnapshot(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_usage=disk_usage,
            network_io=network_stats,
            container_stats=container_stats or {}
        )

        self.snapshots.append(snapshot)

    def record_operation_timing(self, operation: str, duration: float) -> None:
        """Record the timing of a specific operation."""
        self.operation_timings[operation] = duration
        logger.debug(f"Recorded operation timing: {operation} = {duration:.2f}s")

    def time_operation(self, operation_name: str):
        """Context manager for timing operations."""
        class Timer:
            def __init__(self, monitor: 'PerformanceMonitor', name: str):
                self.monitor = monitor
                self.name = name
                self.start_time = None

            def __enter__(self):
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.start_time is not None:
                    duration = time.time() - self.start_time
                    self.monitor.record_operation_timing(self.name, duration)

        return Timer(self, operation_name)

    def _load_baseline(self) -> None:
        """Load baseline performance data."""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, 'r') as f:
                    self.baseline_data = json.load(f)
                logger.info(f"Loaded baseline data from {self.baseline_file}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load baseline data: {e}")
        else:
            logger.info("No baseline data file found")

    def _detect_regressions(self, duration: float, peak_memory: float, avg_cpu: float) -> List[str]:
        """Detect performance regressions compared to baseline."""
        if not self.baseline_data:
            return []

        regressions = []

        # Check duration regression
        baseline_duration = self.baseline_data.get("average_duration", duration)
        if duration > baseline_duration * 1.2:  # 20% increase
            regressions.append(f"Duration regression: {duration:.2f}s vs baseline {baseline_duration:.2f}s")

        # Check memory regression
        baseline_memory = self.baseline_data.get("peak_memory", peak_memory)
        if peak_memory > baseline_memory * 1.1:  # 10% increase
            regressions.append(f"Memory regression: {peak_memory:.1f}% vs baseline {baseline_memory:.1f}%")

        # Check CPU regression
        baseline_cpu = self.baseline_data.get("average_cpu", avg_cpu)
        if avg_cpu > baseline_cpu * 1.15:  # 15% increase
            regressions.append(f"CPU regression: {avg_cpu:.1f}% vs baseline {baseline_cpu:.1f}%")

        return regressions

    def save_report(self, report: PerformanceReport, output_file: Path) -> None:
        """Save performance report to file."""
        report_data = {
            "test_name": report.test_name,
            "start_time": report.start_time.isoformat(),
            "end_time": report.end_time.isoformat(),
            "duration": report.duration,
            "peak_memory_usage": report.peak_memory_usage,
            "average_cpu_usage": report.average_cpu_usage,
            "total_network_io": report.total_network_io,
            "operation_timings": report.operation_timings,
            "regressions_detected": report.regressions_detected,
            "snapshot_count": len(report.snapshots)
        }

        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"Saved performance report to {output_file}")

    def update_baseline(self, report: PerformanceReport) -> None:
        """Update baseline data with current performance metrics."""
        baseline_data = {
            "test_name": report.test_name,
            "average_duration": report.duration,
            "peak_memory": report.peak_memory_usage,
            "average_cpu": report.average_cpu_usage,
            "total_network_bytes_sent": report.total_network_io["bytes_sent"],
            "total_network_bytes_recv": report.total_network_io["bytes_recv"],
            "operation_timings": report.operation_timings,
            "updated_at": datetime.now().isoformat()
        }

        with open(self.baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2, default=str)

        logger.info(f"Updated baseline data in {self.baseline_file}")


class ContainerMonitor:
    """Monitors container-specific performance metrics."""

    def __init__(self, container_name: str):
        self.container_name = container_name

    def get_container_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the container."""
        # This would use LXC tools to get container-specific metrics
        # For now, return mock data
        return {
            "cpu_usage": 15.5,
            "memory_usage": 256 * 1024 * 1024,  # 256MB
            "disk_read_bytes": 1024 * 1024,
            "disk_write_bytes": 512 * 1024,
            "network_rx_bytes": 64 * 1024,
            "network_tx_bytes": 32 * 1024
        }


def collect_system_baseline(test_name: str, duration: int = 60) -> Dict[str, Any]:
    """Collect baseline system performance over a period."""
    logger.info(f"Collecting baseline for {test_name} over {duration}s")

    monitor = PerformanceMonitor()
    monitor.start_monitoring(f"{test_name}_baseline")

    # Collect snapshots over time
    for i in range(duration // 5):  # Every 5 seconds
        monitor.take_snapshot()
        time.sleep(5)

    report = monitor.stop_monitoring()

    # Calculate averages
    baseline = {
        "test_name": test_name,
        "collection_duration": duration,
        "average_cpu": report.average_cpu_usage,
        "peak_memory": report.peak_memory_usage,
        "average_network_bytes_sent": report.total_network_io["bytes_sent"] / duration,
        "average_network_bytes_recv": report.total_network_io["bytes_recv"] / duration,
        "collected_at": datetime.now().isoformat()
    }

    return baseline