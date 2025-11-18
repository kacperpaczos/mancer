#!/usr/bin/env python3
"""
Log Analyzer for E2E Tests.

This script analyzes logs from E2E test execution to identify patterns,
errors, performance issues, and provide insights for debugging.
"""

import argparse
import re
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Pattern, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter


logger = logging.getLogger(__name__)


class LogAnalyzer:
    """Analyzes E2E test logs for patterns and insights."""

    def __init__(self, log_files: List[Path]):
        self.log_files = log_files
        self.entries: List[Dict[str, Any]] = []
        self.patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, Pattern]:
        """Compile regex patterns for log analysis."""
        return {
            # Error patterns
            "error": re.compile(r"(?i)(error|exception|fail|critical)", re.IGNORECASE),
            "warning": re.compile(r"(?i)(warning|warn)", re.IGNORECASE),

            # Performance patterns
            "performance": re.compile(r"(?i)(performance|latency|throughput|bottleneck)", re.IGNORECASE),
            "timing": re.compile(r"(\d+\.?\d*)\s*(ms|s|seconds?)", re.IGNORECASE),

            # Container patterns
            "container_start": re.compile(r"(?i)(container.*start|starting.*container)", re.IGNORECASE),
            "container_stop": re.compile(r"(?i)(container.*stop|stopping.*container)", re.IGNORECASE),

            # Network patterns
            "network_error": re.compile(r"(?i)(connection.*fail|network.*error|timeout)", re.IGNORECASE),

            # Test patterns
            "test_start": re.compile(r"(?i)(test.*start|starting.*test)", re.IGNORECASE),
            "test_end": re.compile(r"(?i)(test.*end|finished.*test)", re.IGNORECASE),
            "test_failure": re.compile(r"(?i)(test.*fail|assertion.*error)", re.IGNORECASE),
        }

    def parse_logs(self) -> None:
        """Parse all log files and extract entries."""
        for log_file in self.log_files:
            if not log_file.exists():
                logger.warning(f"Log file not found: {log_file}")
                continue

            logger.info(f"Parsing log file: {log_file}")

            try:
                with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                    for line_num, line in enumerate(f, 1):
                        entry = self._parse_log_line(line.strip(), log_file.name, line_num)
                        if entry:
                            self.entries.append(entry)
            except IOError as e:
                logger.error(f"Failed to read log file {log_file}: {e}")

        logger.info(f"Parsed {len(self.entries)} log entries")

    def _parse_log_line(self, line: str, filename: str, line_num: int) -> Optional[Dict[str, Any]]:
        """Parse a single log line."""
        if not line.strip():
            return None

        # Common log format patterns
        patterns = [
            # ISO timestamp format
            r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+(.+)",
            # Standard timestamp format
            r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d{3})?)\s+(.+)",
            # Simple format
            r"(\w+)\s+(.+)",
        ]

        timestamp = None
        message = line

        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                timestamp_str, message = match.groups()
                try:
                    # Try to parse timestamp
                    if 'T' in timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    timestamp = None
                break

        # Classify the log entry
        level = self._classify_log_level(message)
        categories = self._categorize_message(message)

        return {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "categories": categories,
            "file": filename,
            "line": line_num,
            "raw": line
        }

    def _classify_log_level(self, message: str) -> str:
        """Classify log level based on message content."""
        message_lower = message.lower()

        if any(word in message_lower for word in ["error", "exception", "critical", "fatal"]):
            return "ERROR"
        elif any(word in message_lower for word in ["warning", "warn"]):
            return "WARNING"
        elif any(word in message_lower for word in ["info", "information"]):
            return "INFO"
        elif any(word in message_lower for word in ["debug", "trace"]):
            return "DEBUG"
        else:
            return "UNKNOWN"

    def _categorize_message(self, message: str) -> List[str]:
        """Categorize message based on patterns."""
        categories = []

        for category, pattern in self.patterns.items():
            if pattern.search(message):
                categories.append(category)

        return categories

    def generate_report(self, output_file: Path) -> Dict[str, Any]:
        """Generate comprehensive log analysis report."""
        logger.info("Generating log analysis report")

        # Basic statistics
        total_entries = len(self.entries)
        level_counts = Counter(entry["level"] for entry in self.entries)
        category_counts = Counter()

        for entry in self.entries:
            category_counts.update(entry["categories"])

        # Time analysis
        timestamps = [e["timestamp"] for e in self.entries if e["timestamp"]]
        time_span = None
        if len(timestamps) > 1:
            time_span = max(timestamps) - min(timestamps)

        # Error analysis
        errors = [e for e in self.entries if e["level"] == "ERROR"]
        error_patterns = self._analyze_error_patterns(errors)

        # Performance analysis
        performance_entries = [e for e in self.entries if "performance" in e["categories"]]
        timing_entries = [e for e in self.entries if "timing" in e["categories"]]

        # Container analysis
        container_events = self._analyze_container_events()

        # Network analysis
        network_issues = [e for e in self.entries if "network_error" in e["categories"]]

        report = {
            "summary": {
                "total_entries": total_entries,
                "time_span": str(time_span) if time_span else None,
                "log_files": len(self.log_files),
                "levels": dict(level_counts),
                "categories": dict(category_counts)
            },
            "errors": {
                "count": len(errors),
                "patterns": error_patterns[:10],  # Top 10 patterns
                "sample_errors": [e["message"] for e in errors[:5]]  # First 5 errors
            },
            "performance": {
                "entries_count": len(performance_entries),
                "timing_entries": len(timing_entries),
                "bottlenecks": self._identify_bottlenecks()
            },
            "containers": container_events,
            "network": {
                "issues_count": len(network_issues),
                "sample_issues": [e["message"] for e in network_issues[:3]]
            },
            "recommendations": self._generate_recommendations(
                errors, performance_entries, network_issues
            ),
            "generated_at": datetime.now().isoformat()
        }

        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Generated log analysis report: {output_file}")
        return report

    def _analyze_error_patterns(self, errors: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
        """Analyze patterns in error messages."""
        error_messages = [e["message"] for e in errors]
        patterns = []

        # Common error patterns
        common_patterns = [
            r"connection.*(?:timeout|refused|failed)",
            r"container.*not.*running",
            r"permission.*denied",
            r"command.*not.*found",
            r"out.*memory",
            r"disk.*full",
        ]

        for pattern in common_patterns:
            regex = re.compile(pattern, re.IGNORECASE)
            count = sum(1 for msg in error_messages if regex.search(msg))
            if count > 0:
                patterns.append((pattern, count))

        # Sort by frequency
        return sorted(patterns, key=lambda x: x[1], reverse=True)

    def _analyze_container_events(self) -> Dict[str, Any]:
        """Analyze container-related events."""
        container_starts = [e for e in self.entries if "container_start" in e["categories"]]
        container_stops = [e for e in self.entries if "container_stop" in e["categories"]]

        return {
            "starts": len(container_starts),
            "stops": len(container_stops),
            "active_containers": len(container_starts) - len(container_stops)
        }

    def _identify_bottlenecks(self) -> List[str]:
        """Identify potential performance bottlenecks."""
        bottlenecks = []

        # Look for timing patterns
        timing_messages = [e["message"] for e in self.entries if "timing" in e["categories"]]

        # Look for repeated slow operations
        slow_operations = []
        for msg in timing_messages:
            match = re.search(r"(\d+(?:\.\d+)?)\s*s", msg)
            if match:
                duration = float(match.group(1))
                if duration > 10:  # Operations taking more than 10 seconds
                    slow_operations.append(f"{duration}s: {msg}")

        bottlenecks.extend(slow_operations[:5])  # Top 5 slowest operations

        return bottlenecks

    def _generate_recommendations(self, errors: List[Dict], performance: List[Dict],
                                network: List[Dict]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        if len(errors) > 10:
            recommendations.append("High error rate detected. Review error handling and retry logic.")

        if len(network) > 5:
            recommendations.append("Network connectivity issues detected. Check network configuration and firewall rules.")

        if len(performance) > 0:
            recommendations.append("Performance monitoring active. Review timing data for optimization opportunities.")

        container_events = self._analyze_container_events()
        if container_events["active_containers"] < 0:
            recommendations.append("Container lifecycle issues detected. Check container startup/shutdown procedures.")

        if not recommendations:
            recommendations.append("Log analysis completed successfully. No critical issues detected.")

        return recommendations

    def print_summary(self, report: Dict[str, Any]) -> None:
        """Print a human-readable summary of the analysis."""
        print("\n" + "="*60)
        print("E2E LOG ANALYSIS SUMMARY")
        print("="*60)

        summary = report["summary"]
        print(f"\nTotal Log Entries: {summary['total_entries']}")
        print(f"Time Span: {summary['time_span'] or 'Unknown'}")
        print(f"Log Files Analyzed: {summary['log_files']}")

        print(f"\nLog Levels: {summary['levels']}")
        print(f"Categories: {summary['categories']}")

        errors = report["errors"]
        print(f"\nErrors Found: {errors['count']}")
        if errors["patterns"]:
            print("Top Error Patterns:")
            for pattern, count in errors["patterns"][:3]:
                print(f"  • {pattern}: {count} occurrences")

        performance = report["performance"]
        print(f"\nPerformance Entries: {performance['entries_count']}")
        if performance["bottlenecks"]:
            print("Performance Bottlenecks:")
            for bottleneck in performance["bottlenecks"][:3]:
                print(f"  • {bottleneck}")

        containers = report["containers"]
        print(f"\nContainer Events: {containers['starts']} starts, {containers['stops']} stops")
        print(f"Active Containers: {containers['active_containers']}")

        network = report["network"]
        print(f"\nNetwork Issues: {network['issues_count']}")

        print(f"\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")


def main():
    """Main entry point for log analysis."""
    parser = argparse.ArgumentParser(description="Analyze E2E test logs")
    parser.add_argument("--log-files", nargs="+", required=True, type=Path,
                       help="Log files to analyze")
    parser.add_argument("--output", type=Path, default=Path("log_analysis_report.json"),
                       help="Output file for analysis report")
    parser.add_argument("--summary-only", action="store_true",
                       help="Print summary without saving detailed report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

    # Analyze logs
    analyzer = LogAnalyzer(args.log_files)
    analyzer.parse_logs()

    if analyzer.entries:
        report = analyzer.generate_report(args.output)

        if args.summary_only:
            analyzer.print_summary(report)
        else:
            analyzer.print_summary(report)
            print(f"\nDetailed report saved to: {args.output}")
    else:
        print("No log entries found to analyze")


if __name__ == "__main__":
    main()