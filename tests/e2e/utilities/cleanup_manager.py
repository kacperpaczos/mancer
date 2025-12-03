#!/usr/bin/env python3
"""
Cleanup Manager for E2E Tests.

This script manages cleanup of resources created during E2E test execution,
ensuring proper teardown and resource reclamation.
"""

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class CleanupManager:
    """Manages cleanup of E2E test resources."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.lxc_available = self._check_lxc_available()

    def _check_lxc_available(self) -> bool:
        """Check if LXC tools are available."""
        try:
            subprocess.run(["lxc-ls", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def cleanup_containers(self, container_pattern: str = "mancer-e2e-*") -> Dict[str, Any]:
        """Clean up LXC containers matching pattern."""
        logger.info(f"Cleaning up containers matching: {container_pattern}")

        if not self.lxc_available:
            logger.warning("LXC tools not available, skipping container cleanup")
            return {"skipped": True, "reason": "LXC not available"}

        try:
            # Get list of containers
            result = subprocess.run(
                ["lxc-ls", "-1"],
                capture_output=True,
                text=True,
                check=True
            )

            containers = result.stdout.strip().split("\n")
            containers_to_cleanup = [c for c in containers if c and container_pattern.replace("*", "") in c]

            cleaned = []
            for container in containers_to_cleanup:
                if self._cleanup_single_container(container):
                    cleaned.append(container)

            return {
                "containers_found": len(containers_to_cleanup),
                "containers_cleaned": len(cleaned),
                "success": True
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list containers: {e}")
            return {"success": False, "error": str(e)}

    def _cleanup_single_container(self, container_name: str) -> bool:
        """Clean up a single container."""
        logger.info(f"Cleaning up container: {container_name}")

        if self.dry_run:
            logger.info(f"[DRY RUN] Would stop and destroy container: {container_name}")
            return True

        try:
            # Stop container if running
            try:
                subprocess.run(["sudo", "lxc-stop", "-n", container_name],
                             capture_output=True, timeout=30)
                logger.debug(f"Stopped container: {container_name}")
            except subprocess.CalledProcessError:
                logger.debug(f"Container {container_name} was not running")

            # Destroy container
            subprocess.run(["sudo", "lxc-destroy", "-n", container_name],
                         capture_output=True, check=True)
            logger.info(f"Destroyed container: {container_name}")

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to cleanup container {container_name}: {e}")
            return False

    def cleanup_files(self, paths: List[Path], age_days: Optional[int] = None) -> Dict[str, Any]:
        """Clean up files and directories."""
        logger.info(f"Cleaning up files in paths: {[str(p) for p in paths]}")

        cleaned_files = 0
        cleaned_dirs = 0
        errors = []

        cutoff_time = None
        if age_days:
            cutoff_time = datetime.now() - timedelta(days=age_days)

        for base_path in paths:
            if not base_path.exists():
                logger.debug(f"Path does not exist: {base_path}")
                continue

            try:
                for item in base_path.rglob("*"):
                    # Check age if specified
                    if cutoff_time and item.exists():
                        mtime = datetime.fromtimestamp(item.stat().st_mtime)
                        if mtime > cutoff_time:
                            continue

                    if self.dry_run:
                        logger.info(f"[DRY RUN] Would remove: {item}")
                        if item.is_file():
                            cleaned_files += 1
                        elif item.is_dir():
                            cleaned_dirs += 1
                    else:
                        try:
                            if item.is_file():
                                item.unlink()
                                cleaned_files += 1
                            elif item.is_dir():
                                shutil.rmtree(item)
                                cleaned_dirs += 1
                        except OSError as e:
                            errors.append(f"Failed to remove {item}: {e}")

                # Remove the base directory itself if it's empty
                if not self.dry_run and base_path.exists():
                    try:
                        base_path.rmdir()
                        logger.info(f"Removed empty directory: {base_path}")
                    except OSError:
                        pass  # Directory not empty, that's fine

            except OSError as e:
                errors.append(f"Failed to process {base_path}: {e}")

        result = {
            "files_cleaned": cleaned_files,
            "directories_cleaned": cleaned_dirs,
            "errors": errors,
            "success": len(errors) == 0
        }

        logger.info(f"File cleanup completed: {cleaned_files} files, {cleaned_dirs} directories")
        return result

    def cleanup_processes(self, process_patterns: List[str]) -> Dict[str, Any]:
        """Clean up processes matching patterns."""
        logger.info(f"Cleaning up processes matching: {process_patterns}")

        if self.dry_run:
            logger.info("[DRY RUN] Would search for and kill processes")
            return {"dry_run": True}

        killed_processes = 0
        errors = []

        try:
            # Get process list
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                check=True
            )

            lines = result.stdout.strip().split("\n")[1:]  # Skip header

            for line in lines:
                parts = line.split()
                if len(parts) < 11:
                    continue

                pid = parts[1]
                command = " ".join(parts[10:])

                # Check if command matches any pattern
                for pattern in process_patterns:
                    if pattern in command:
                        try:
                            subprocess.run(["kill", "-TERM", pid], capture_output=True)
                            logger.info(f"Killed process {pid}: {command}")
                            killed_processes += 1
                        except subprocess.CalledProcessError as e:
                            errors.append(f"Failed to kill process {pid}: {e}")
                        break

        except subprocess.CalledProcessError as e:
            errors.append(f"Failed to get process list: {e}")

        return {
            "processes_killed": killed_processes,
            "errors": errors,
            "success": len(errors) == 0
        }

    def cleanup_network(self, bridge_name: str = "lxcbr0") -> Dict[str, Any]:
        """Clean up network bridges and rules."""
        logger.info(f"Cleaning up network bridge: {bridge_name}")

        if not self.lxc_available:
            logger.warning("LXC tools not available, skipping network cleanup")
            return {"skipped": True, "reason": "LXC not available"}

        if self.dry_run:
            logger.info(f"[DRY RUN] Would remove network bridge: {bridge_name}")
            return {"dry_run": True}

        try:
            # Check if bridge exists
            result = subprocess.run(
                ["ip", "link", "show", bridge_name],
                capture_output=True
            )

            if result.returncode == 0:
                # Bridge exists, try to remove it
                try:
                    subprocess.run(["sudo", "ip", "link", "set", bridge_name, "down"],
                                 capture_output=True, check=True)
                    subprocess.run(["sudo", "ip", "link", "delete", bridge_name],
                                 capture_output=True, check=True)
                    logger.info(f"Removed network bridge: {bridge_name}")
                    return {"success": True, "bridge_removed": True}
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to remove bridge {bridge_name}: {e}")
                    return {"success": False, "error": str(e)}
            else:
                logger.debug(f"Bridge {bridge_name} does not exist")
                return {"success": True, "bridge_removed": False}

        except Exception as e:
            logger.error(f"Network cleanup failed: {e}")
            return {"success": False, "error": str(e)}

    def comprehensive_cleanup(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive cleanup based on configuration."""
        logger.info("Starting comprehensive E2E cleanup")

        results = {}

        # Cleanup containers
        if config.get("cleanup_containers", True):
            container_pattern = config.get("container_pattern", "mancer-e2e-*")
            results["containers"] = self.cleanup_containers(container_pattern)

        # Cleanup files
        if config.get("cleanup_files", True):
            cleanup_paths = config.get("cleanup_paths", [
                Path("/tmp/e2e_workspace"),
                Path("/tmp/integration_workspace"),
                Path("performance_reports"),
                Path("e2e_test.log")
            ])
            age_days = config.get("cleanup_age_days")
            results["files"] = self.cleanup_files(cleanup_paths, age_days)

        # Cleanup processes
        if config.get("cleanup_processes", True):
            process_patterns = config.get("process_patterns", [
                "pytest.*e2e",
                "lxc-attach",
                "container_setup.sh"
            ])
            results["processes"] = self.cleanup_processes(process_patterns)

        # Cleanup network
        if config.get("cleanup_network", True):
            bridge_name = config.get("bridge_name", "lxcbr0")
            results["network"] = self.cleanup_network(bridge_name)

        # Overall success
        all_success = all(r.get("success", False) for r in results.values()
                         if isinstance(r, dict) and "success" in r)

        results["overall_success"] = all_success

        logger.info(f"Comprehensive cleanup completed: {'SUCCESS' if all_success else 'ISSUES DETECTED'}")
        return results


def main():
    """Main entry point for cleanup operations."""
    parser = argparse.ArgumentParser(description="Clean up E2E test resources")
    parser.add_argument("--containers", action="store_true",
                       help="Clean up LXC containers")
    parser.add_argument("--container-pattern", default="mancer-e2e-*",
                       help="Pattern for containers to cleanup")
    parser.add_argument("--files", action="store_true",
                       help="Clean up test files and directories")
    parser.add_argument("--cleanup-paths", nargs="+", type=Path,
                       default=[Path("/tmp/e2e_workspace"), Path("performance_reports")],
                       help="Paths to cleanup")
    parser.add_argument("--age-days", type=int,
                       help="Only cleanup files older than this many days")
    parser.add_argument("--processes", action="store_true",
                       help="Clean up test processes")
    parser.add_argument("--process-patterns", nargs="+",
                       default=["pytest.*e2e", "lxc-attach"],
                       help="Process patterns to cleanup")
    parser.add_argument("--network", action="store_true",
                       help="Clean up network bridges")
    parser.add_argument("--bridge-name", default="lxcbr0",
                       help="Network bridge to cleanup")
    parser.add_argument("--comprehensive", action="store_true",
                       help="Perform comprehensive cleanup of all resources")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be cleaned without actually doing it")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

    manager = CleanupManager(dry_run=args.dry_run)

    if args.comprehensive:
        # Comprehensive cleanup
        config = {
            "cleanup_containers": True,
            "container_pattern": args.container_pattern,
            "cleanup_files": True,
            "cleanup_paths": args.cleanup_paths,
            "cleanup_age_days": args.age_days,
            "cleanup_processes": True,
            "process_patterns": args.process_patterns,
            "cleanup_network": True,
            "bridge_name": args.bridge_name
        }

        results = manager.comprehensive_cleanup(config)

        print(f"\nComprehensive cleanup {'completed successfully' if results['overall_success'] else 'had issues'}")
        print("\nDetailed results:")
        for category, result in results.items():
            if category != "overall_success":
                if isinstance(result, dict):
                    status = "✓" if result.get("success") else "✗"
                    print(f"  {category}: {status}")
                    if not result.get("success") and "error" in result:
                        print(f"    Error: {result['error']}")

    else:
        # Individual cleanup operations
        results = {}

        if args.containers:
            results["containers"] = manager.cleanup_containers(args.container_pattern)

        if args.files:
            results["files"] = manager.cleanup_files(args.cleanup_paths, args.age_days)

        if args.processes:
            results["processes"] = manager.cleanup_processes(args.process_patterns)

        if args.network:
            results["network"] = manager.cleanup_network(args.bridge_name)

        if not results:
            print("No cleanup operations specified. Use --help for options.")
            sys.exit(1)

        # Print results
        print("\nCleanup Results:")
        for category, result in results.items():
            if isinstance(result, dict) and "success" in result:
                status = "✓ SUCCESS" if result["success"] else "✗ FAILED"
                print(f"  {category}: {status}")
                if not result["success"] and "error" in result:
                    print(f"    Error: {result['error']}")

    # Exit with appropriate code
    if not args.dry_run:
        success = all(r.get("success", True) for r in results.values()
                     if isinstance(r, dict))
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
