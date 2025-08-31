"""
Observability Core - Główny komponent observability
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ObservabilityTarget:
    """Cel observability - serwer, usługa, aplikacja"""

    id: str
    name: str
    type: str  # server, service, application, database
    hostname: str
    ip_address: str
    environment: str
    group: str
    status: str = "unknown"
    last_check: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObservabilityMetric:
    """Metryka observability"""

    target_id: str
    metric_name: str
    metric_value: float
    metric_unit: str
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


class ObservabilityCore:
    """Główna klasa observability"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.targets: Dict[str, ObservabilityTarget] = {}
        self.metrics: List[ObservabilityMetric] = []
        self.logger = logging.getLogger("mancerops.observability")

    def add_target(self, target: ObservabilityTarget) -> None:
        """Dodaje cel observability"""
        self.targets[target.id] = target
        self.logger.info(f"Dodano cel observability: {target.name} ({target.type})")

    def collect_metrics(self, target_id: str, metrics: List[ObservabilityMetric]) -> None:
        """Zbiera metryki z celu"""
        for metric in metrics:
            metric.target_id = target_id
            metric.timestamp = datetime.now()
            self.metrics.append(metric)

        self.logger.debug(f"Zebrano {len(metrics)} metryk z {target_id}")

    def get_target_metrics(
        self, target_id: str, metric_name: Optional[str] = None, limit: int = 100
    ) -> List[ObservabilityMetric]:
        """Pobiera metryki dla celu"""
        filtered_metrics = [m for m in self.metrics if m.target_id == target_id]

        if metric_name:
            filtered_metrics = [m for m in filtered_metrics if m.metric_name == metric_name]

        # Sortuj po timestamp i zwróć ostatnie
        filtered_metrics.sort(key=lambda x: x.timestamp, reverse=True)
        return filtered_metrics[:limit]

    def get_targets_by_group(self, group: str) -> List[ObservabilityTarget]:
        """Pobiera cele według grupy"""
        return [target for target in self.targets.values() if target.group == group]

    def get_targets_by_environment(self, environment: str) -> List[ObservabilityTarget]:
        """Pobiera cele według środowiska"""
        return [target for target in self.targets.values() if target.environment == environment]

    def update_target_status(self, target_id: str, status: str) -> None:
        """Aktualizuje status celu"""
        if target_id in self.targets:
            self.targets[target_id].status = status
            self.targets[target_id].last_check = datetime.now()
            self.logger.info(f"Zaktualizowano status {target_id}: {status}")

    def get_health_summary(self) -> Dict[str, Any]:
        """Zwraca podsumowanie zdrowia wszystkich celów"""
        total_targets = len(self.targets)
        healthy_targets = len([t for t in self.targets.values() if t.status == "healthy"])
        warning_targets = len([t for t in self.targets.values() if t.status == "warning"])
        critical_targets = len([t for t in self.targets.values() if t.status == "critical"])

        return {
            "total": total_targets,
            "healthy": healthy_targets,
            "warning": warning_targets,
            "critical": critical_targets,
            "health_percentage": (
                (healthy_targets / total_targets * 100) if total_targets > 0 else 0
            ),
        }
