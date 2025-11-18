#!/usr/bin/env python3
"""
Baseline Performance Collector for E2E Tests.

This script collects baseline performance metrics for E2E test scenarios
to establish performance expectations and detect regressions.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.e2e.lxc.monitoring import PerformanceMonitor, collect_system_baseline


logger = logging.getLogger(__name__)


class BaselineCollector:
    """Collects and manages performance baselines for E2E tests."""

    def __init__(self, baseline_dir: Path):
        self.baseline_dir = baseline_dir
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

    def collect_test_baseline(self, test_name: str, duration: int = 60) -> Dict[str, Any]:
        """Collect baseline for a specific test scenario."""
        logger.info(f"Collecting baseline for test: {test_name}")

        baseline = collect_system_baseline(test_name, duration)

        # Save baseline
        baseline_file = self.baseline_dir / f"{test_name}_baseline.json"
        with open(baseline_file, 'w') as f:
            json.dump(baseline, f, indent=2, default=str)

        logger.info(f"Saved baseline to {baseline_file}")
        return baseline

    def collect_scenario_baselines(self, scenario: str, tests: List[str]) -> Dict[str, Any]:
        """Collect baselines for all tests in a scenario."""
        logger.info(f"Collecting baselines for scenario: {scenario}")

        scenario_baselines = {
            "scenario": scenario,
            "collected_at": datetime.now().isoformat(),
            "tests": {}
        }

        for test in tests:
            try:
                baseline = self.collect_test_baseline(test)
                scenario_baselines["tests"][test] = baseline
                logger.info(f"Collected baseline for {test}")
            except Exception as e:
                logger.error(f"Failed to collect baseline for {test}: {e}")
                scenario_baselines["tests"][test] = {"error": str(e)}

        # Save scenario baseline
        scenario_file = self.baseline_dir / f"{scenario}_scenario_baseline.json"
        with open(scenario_file, 'w') as f:
            json.dump(scenario_baselines, f, indent=2, default=str)

        logger.info(f"Saved scenario baseline to {scenario_file}")
        return scenario_baselines

    def compare_with_baseline(self, test_name: str, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current metrics with stored baseline."""
        baseline_file = self.baseline_dir / f"{test_name}_baseline.json"

        if not baseline_file.exists():
            logger.warning(f"No baseline found for {test_name}")
            return {"comparison": "no_baseline", "regressions": []}

        try:
            with open(baseline_file, 'r') as f:
                baseline = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load baseline: {e}")
            return {"comparison": "error", "error": str(e), "regressions": []}

        # Compare metrics
        regressions = []
        comparisons = {}

        # CPU comparison
        current_cpu = current_metrics.get("average_cpu", 0)
        baseline_cpu = baseline.get("average_cpu", 0)
        cpu_diff = ((current_cpu - baseline_cpu) / baseline_cpu) * 100 if baseline_cpu > 0 else 0
        comparisons["cpu"] = {
            "current": current_cpu,
            "baseline": baseline_cpu,
            "difference_percent": cpu_diff
        }
        if cpu_diff > 15:  # 15% regression threshold
            regressions.append(f"CPU usage increased by {cpu_diff:.1f}%")

        # Memory comparison
        current_mem = current_metrics.get("peak_memory", 0)
        baseline_mem = baseline.get("peak_memory", 0)
        mem_diff = ((current_mem - baseline_mem) / baseline_mem) * 100 if baseline_mem > 0 else 0
        comparisons["memory"] = {
            "current": current_mem,
            "baseline": baseline_mem,
            "difference_percent": mem_diff
        }
        if mem_diff > 10:  # 10% regression threshold
            regressions.append(f"Memory usage increased by {mem_diff:.1f}%")

        # Duration comparison (if available)
        current_duration = current_metrics.get("duration", 0)
        baseline_duration = baseline.get("average_duration", 0)
        if baseline_duration > 0:
            duration_diff = ((current_duration - baseline_duration) / baseline_duration) * 100
            comparisons["duration"] = {
                "current": current_duration,
                "baseline": baseline_duration,
                "difference_percent": duration_diff
            }
            if duration_diff > 20:  # 20% regression threshold
                regressions.append(f"Duration increased by {duration_diff:.1f}%")

        result = {
            "comparison": "completed",
            "regressions": regressions,
            "comparisons": comparisons,
            "baseline_date": baseline.get("collected_at"),
            "current_date": datetime.now().isoformat()
        }

        if regressions:
            logger.warning(f"Performance regressions detected for {test_name}: {regressions}")
        else:
            logger.info(f"No performance regressions detected for {test_name}")

        return result

    def list_baselines(self) -> List[Dict[str, Any]]:
        """List all available baselines."""
        baselines = []

        for baseline_file in self.baseline_dir.glob("*_baseline.json"):
            try:
                with open(baseline_file, 'r') as f:
                    baseline = json.load(f)
                baselines.append({
                    "name": baseline_file.stem.replace("_baseline", ""),
                    "file": str(baseline_file),
                    "collected_at": baseline.get("collected_at", "unknown"),
                    "scenario": baseline.get("scenario", "single_test")
                })
            except (json.JSONDecodeError, IOError):
                continue

        return baselines

    def cleanup_old_baselines(self, days: int = 30) -> int:
        """Clean up baselines older than specified days."""
        import shutil
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        removed_count = 0

        for baseline_file in self.baseline_dir.glob("*_baseline.json"):
            try:
                with open(baseline_file, 'r') as f:
                    baseline = json.load(f)

                collected_at = baseline.get("collected_at")
                if collected_at:
                    collected_date = datetime.fromisoformat(collected_at.replace('Z', '+00:00'))
                    if collected_date < cutoff_date:
                        baseline_file.unlink()
                        removed_count += 1
                        logger.info(f"Removed old baseline: {baseline_file}")
            except (json.JSONDecodeError, IOError, ValueError):
                continue

        return removed_count


def main():
    """Main entry point for baseline collection."""
    parser = argparse.ArgumentParser(description="Collect performance baselines for E2E tests")
    parser.add_argument("--baseline-dir", type=Path, default=Path("tests/e2e/baselines"),
                       help="Directory to store baseline files")
    parser.add_argument("--test-name", help="Specific test to collect baseline for")
    parser.add_argument("--scenario", help="Scenario to collect baselines for")
    parser.add_argument("--duration", type=int, default=60,
                       help="Duration in seconds to collect baseline")
    parser.add_argument("--list", action="store_true", help="List available baselines")
    parser.add_argument("--cleanup", type=int, metavar="DAYS",
                       help="Clean up baselines older than DAYS")
    parser.add_argument("--compare", help="Compare current run with baseline")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

    collector = BaselineCollector(args.baseline_dir)

    if args.list:
        baselines = collector.list_baselines()
        print(f"Available baselines ({len(baselines)}):")
        for baseline in baselines:
            print(f"  {baseline['name']} - {baseline['collected_at']} ({baseline['scenario']})")

    elif args.cleanup:
        removed = collector.cleanup_old_baselines(args.cleanup)
        print(f"Removed {removed} old baseline files")

    elif args.compare:
        # This would typically read metrics from a file or stdin
        print("Compare functionality requires metrics input (not implemented)")

    elif args.scenario:
        # Define tests for each scenario
        scenario_tests = {
            "data_pipeline": [
                "test_data_ingestion_e2e",
                "test_batch_processing_e2e",
                "test_data_transformation_e2e"
            ],
            "automation_workflows": [
                "test_deployment_workflow_e2e",
                "test_backup_workflow_e2e",
                "test_monitoring_workflow_e2e"
            ],
            "error_handling": [
                "test_failure_recovery_e2e",
                "test_graceful_degradation_e2e",
                "test_chaos_engineering_e2e"
            ]
        }

        if args.scenario not in scenario_tests:
            print(f"Unknown scenario: {args.scenario}")
            print(f"Available scenarios: {list(scenario_tests.keys())}")
            sys.exit(1)

        tests = scenario_tests[args.scenario]
        logger.info(f"Collecting baselines for scenario '{args.scenario}' with tests: {tests}")

        result = collector.collect_scenario_baselines(args.scenario, tests)
        print(f"Collected baselines for scenario '{args.scenario}'")

    elif args.test_name:
        logger.info(f"Collecting baseline for test '{args.test_name}'")
        baseline = collector.collect_test_baseline(args.test_name, args.duration)
        print(f"Collected baseline for test '{args.test_name}'")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()