#!/usr/bin/env python3
"""
Performance Monitor for E2E Tests.

This script monitors and reports performance metrics during E2E test execution,
providing real-time feedback and detailed analysis.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.e2e.lxc.monitoring import PerformanceMonitor, PerformanceReport


logger = logging.getLogger(__name__)


class E2EPerformanceMonitor:
    """Monitors performance during E2E test execution."""

    def __init__(self, output_dir: Path, baseline_dir: Optional[Path] = None):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.baseline_dir = baseline_dir
        self.monitor = PerformanceMonitor(baseline_dir / "performance_baseline.json" if baseline_dir else None)
        self.current_test: Optional[str] = None

    def start_test(self, test_name: str) -> None:
        """Start monitoring a test."""
        self.current_test = test_name
        self.monitor.start_monitoring(test_name)
        logger.info(f"Started performance monitoring for {test_name}")

    def stop_test(self) -> PerformanceReport:
        """Stop monitoring and generate report."""
        if not self.current_test:
            raise RuntimeError("No test is currently being monitored")

        report = self.monitor.stop_monitoring()

        # Save detailed report
        report_file = self.output_dir / f"{self.current_test}_performance.json"
        self.monitor.save_report(report, report_file)

        # Generate summary report
        summary_file = self.output_dir / f"{self.current_test}_summary.txt"
        self._generate_summary_report(report, summary_file)

        # Check for regressions
        if report.regressions_detected:
            regression_file = self.output_dir / f"{self.current_test}_regressions.txt"
            self._generate_regression_report(report, regression_file)

        logger.info(f"Completed performance monitoring for {self.current_test}")
        self.current_test = None

        return report

    def record_operation(self, operation: str, duration: float) -> None:
        """Record the duration of a specific operation."""
        self.monitor.record_operation_timing(operation, duration)

    def take_snapshot(self, container_stats: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        """Take a performance snapshot."""
        self.monitor.take_snapshot(container_stats)

    def time_operation(self, operation_name: str):
        """Context manager for timing operations."""
        return self.monitor.time_operation(operation_name)

    def _generate_summary_report(self, report: PerformanceReport, output_file: Path) -> None:
        """Generate a human-readable summary report."""
        with open(output_file, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write(f"E2E Performance Summary: {report.test_name}\n")
            f.write("=" * 60 + "\n\n")

            f.write("Execution Summary:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Start Time:     {report.start_time}\n")
            f.write(f"End Time:       {report.end_time}\n")
            f.write(f"Total Duration: {report.duration:.2f} seconds\n\n")

            f.write("Resource Usage:\n")
            f.write("-" * 15 + "\n")
            f.write(f"Peak Memory:    {report.peak_memory_usage:.1f}%\n")
            f.write(f"Average CPU:    {report.average_cpu_usage:.1f}%\n")
            f.write(f"Network Sent:   {report.total_network_io['bytes_sent']:,} bytes\n")
            f.write(f"Network Recv:   {report.total_network_io['bytes_recv']:,} bytes\n\n")

            if report.operation_timings:
                f.write("Operation Timings:\n")
                f.write("-" * 18 + "\n")
                for operation, duration in sorted(report.operation_timings.items()):
                    f.write("30")
                f.write("\n")

            f.write(f"Snapshots Taken: {len(report.snapshots)}\n\n")

            if report.regressions_detected:
                f.write("⚠️  Performance Regressions Detected:\n")
                f.write("-" * 35 + "\n")
                for regression in report.regressions_detected:
                    f.write(f"  • {regression}\n")
                f.write("\nSee regressions file for details.\n")
            else:
                f.write("✅ No performance regressions detected.\n")

        logger.info(f"Generated summary report: {output_file}")

    def _generate_regression_report(self, report: PerformanceReport, output_file: Path) -> None:
        """Generate detailed regression analysis."""
        with open(output_file, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write(f"PERFORMANCE REGRESSIONS: {report.test_name}\n")
            f.write("=" * 60 + "\n\n")

            f.write("⚠️  WARNING: Performance regressions have been detected!\n\n")

            f.write("Regression Details:\n")
            f.write("-" * 20 + "\n")
            for i, regression in enumerate(report.regressions_detected, 1):
                f.write(f"{i}. {regression}\n")
            f.write("\n")

            f.write("Recommendations:\n")
            f.write("-" * 15 + "\n")
            f.write("1. Review recent code changes for performance impacts\n")
            f.write("2. Check system resources during test execution\n")
            f.write("3. Consider optimizing identified bottlenecks\n")
            f.write("4. Update baseline if changes are expected\n")
            f.write("5. Re-run tests to confirm regression persistence\n\n")

            f.write("Test Metrics:\n")
            f.write("-" * 12 + "\n")
            f.write(f"Duration: {report.duration:.2f}s\n")
            f.write(f"Peak Memory: {report.peak_memory_usage:.1f}%\n")
            f.write(f"Average CPU: {report.average_cpu_usage:.1f}%\n")

        logger.warning(f"Generated regression report: {output_file}")

    def generate_comparison_report(self, test_name: str, current_report: PerformanceReport,
                                 baseline_file: Optional[Path] = None) -> None:
        """Generate comparison report with baseline."""
        if not self.baseline_dir or not baseline_file:
            return

        from tests.e2e.utilities.baseline_collector import BaselineCollector
        collector = BaselineCollector(self.baseline_dir)

        current_metrics = {
            "average_cpu": current_report.average_cpu_usage,
            "peak_memory": current_report.peak_memory_usage,
            "duration": current_report.duration
        }

        comparison = collector.compare_with_baseline(test_name, current_metrics)

        comparison_file = self.output_dir / f"{test_name}_comparison.json"
        with open(comparison_file, 'w') as f:
            json.dump(comparison, f, indent=2, default=str)

        if comparison["regressions"]:
            logger.warning(f"Performance comparison completed with regressions: {comparison_file}")
        else:
            logger.info(f"Performance comparison completed: {comparison_file}")


def monitor_test_execution(test_name: str, test_function, output_dir: Path,
                          baseline_dir: Optional[Path] = None, snapshot_interval: int = 5) -> PerformanceReport:
    """Monitor a test function execution with performance tracking."""
    monitor = E2EPerformanceMonitor(output_dir, baseline_dir)
    monitor.start_test(test_name)

    # Start background snapshot collection
    import threading

    def snapshot_worker():
        while monitor.monitor.start_time and not monitor.monitor.end_time:
            monitor.take_snapshot()
            time.sleep(snapshot_interval)

    snapshot_thread = threading.Thread(target=snapshot_worker, daemon=True)
    snapshot_thread.start()

    try:
        # Execute the test function
        with monitor.time_operation("test_execution"):
            test_function()

    finally:
        # Stop monitoring
        report = monitor.stop_test()

        # Generate comparison if baseline available
        if baseline_dir:
            monitor.generate_comparison_report(test_name, report)

        # Wait for snapshot thread to finish
        snapshot_thread.join(timeout=1)

    return report


def main():
    """Main entry point for performance monitoring."""
    parser = argparse.ArgumentParser(description="Monitor E2E test performance")
    parser.add_argument("--test-name", required=True, help="Name of the test to monitor")
    parser.add_argument("--output-dir", type=Path, default=Path("performance_reports"),
                       help="Directory to save performance reports")
    parser.add_argument("--baseline-dir", type=Path, help="Directory containing baseline files")
    parser.add_argument("--snapshot-interval", type=int, default=5,
                       help="Interval in seconds between performance snapshots")
    parser.add_argument("--command", help="Command to execute and monitor")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

    if not args.command:
        print("Error: --command is required")
        sys.exit(1)

    def test_function():
        """Execute the provided command."""
        import subprocess
        result = subprocess.run(args.command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Command failed: {result.stderr}")
            raise RuntimeError(f"Command execution failed: {args.command}")

    # Monitor the command execution
    report = monitor_test_execution(
        args.test_name,
        test_function,
        args.output_dir,
        args.baseline_dir,
        args.snapshot_interval
    )

    # Print summary
    print(f"\nPerformance Summary for {args.test_name}:")
    print(f"Duration: {report.duration:.2f}s")
    print(f"Peak Memory: {report.peak_memory_usage:.1f}%")
    print(f"Average CPU: {report.average_cpu_usage:.1f}%")

    if report.regressions_detected:
        print(f"\n⚠️  Regressions detected: {len(report.regressions_detected)}")
        for regression in report.regressions_detected:
            print(f"  • {regression}")
        sys.exit(1)
    else:
        print("\n✅ No performance regressions detected")


if __name__ == "__main__":
    main()