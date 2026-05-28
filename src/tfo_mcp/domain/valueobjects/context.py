"""Context-related value objects.

TelemetryFlow Python MCP Server - Community Enterprise Observability Platform
Copyright (c) 2024-2026 Telemetri Data Indonesia. All rights reserved.
Open Source Software built by Telemetri Data Indonesia.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class ContextType(StrEnum):
    """TFO Platform context types."""

    METRICS = "metrics"
    LOGS = "logs"
    TRACES = "traces"
    EXEMPLARS = "exemplars"
    CORRELATIONS = "correlations"
    DASHBOARD = "dashboard"
    UPTIME = "uptime"
    STATUS_PAGE = "status-page"
    AUDIT = "audit"
    INFRA_OVERVIEW = "infra-overview"
    INFRA_CPU = "infra-cpu"
    INFRA_MEMORY = "infra-memory"
    INFRA_STORAGE = "infra-storage"
    INFRA_NETWORK = "infra-network"
    KUBERNETES_OVERVIEW = "kubernetes-overview"
    KUBERNETES_CLUSTERS = "kubernetes-clusters"
    KUBERNETES_NAMESPACES = "kubernetes-namespaces"
    KUBERNETES_NODES = "kubernetes-nodes"
    KUBERNETES_PODS = "kubernetes-pods"
    KUBERNETES_DEPLOYMENTS = "kubernetes-deployments"
    KUBERNETES_PV = "kubernetes-pv"
    KUBERNETES_API_SERVER = "kubernetes-api-server"
    KUBERNETES_COREDNS = "kubernetes-coredns"
    AGENTS = "agents"
    SERVICE_MAP = "service-map"
    NETWORK_MAP = "network-map"
    ALERTS = "alerts"
    ALERT_RULES = "alert-rules"
    IAM = "iam"
    IAM_USERS = "iam-users"
    IAM_ROLES = "iam-roles"
    IAM_PERMISSIONS = "iam-permissions"
    IAM_MATRIX = "iam-matrix"
    IAM_ASSIGNMENTS = "iam-assignments"
    TENANCY = "tenancy"
    TENANCY_REGIONS = "tenancy-regions"
    TENANCY_ORGANIZATIONS = "tenancy-organizations"
    TENANCY_WORKSPACES = "tenancy-workspaces"
    TENANCY_TENANTS = "tenancy-tenants"
    RETENTION = "retention"
    SUBSCRIPTION = "subscription"
    API_KEYS = "api-keys"
    NOTIFICATIONS = "notifications"
    REPORTS = "reports"
    DATA_MASKING = "data-masking"
    AI_ASSISTANT = "ai-assistant"
    SYSTEM_SETUP = "system-setup"
    SYSTEM_CHANNELS = "system-channels"
    ACCOUNT_PROFILE = "account-profile"
    ACCOUNT_SECURITY = "account-security"
    ACCOUNT_SESSIONS = "account-sessions"
    ACCOUNT_NOTIFICATIONS = "account-notifications"
    ACCOUNT_PREFERENCES = "account-preferences"
    ACCOUNT_ORGANIZATION = "account-organization"
    ANOMALY_DETECTION = "anomaly-detection"
    CORRECTIVE_MAINTENANCE = "corrective-maintenance"
    PREDICTIVE_MAINTENANCE = "predictive-maintenance"
    COST_OPTIMIZATION = "cost-optimization"
    DB_MONITORING_INVENTORY = "db-monitoring-inventory"
    DB_MONITORING_CLICKHOUSE = "db-monitoring-clickhouse"
    DB_MONITORING_MARIADB = "db-monitoring-mariadb"
    DB_MONITORING_MYSQL = "db-monitoring-mysql"
    DB_MONITORING_PERCONA = "db-monitoring-percona"
    DB_MONITORING_SQLITE3 = "db-monitoring-sqlite3"
    DB_MONITORING_TIMESCALEDB = "db-monitoring-timescaledb"
    DB_MONITORING_AURORA = "db-monitoring-aurora"
    DB_MONITORING_MSSQL = "db-monitoring-mssql"
    DB_MONITORING_POSTGRESQL = "db-monitoring-postgresql"
    DB_MONITORING_MONGODB_COMMUNITY = "db-monitoring-mongodb-community"
    DB_MONITORING_MONGODB_ATLAS = "db-monitoring-mongodb-atlas"
    DB_MONITORING_AWS_RDS_MYSQL = "db-monitoring-aws-rds-mysql"
    DB_MONITORING_AWS_RDS_AURORA = "db-monitoring-aws-rds-aurora"
    DB_MONITORING_AWS_DYNAMODB = "db-monitoring-aws-dynamodb"
    DB_MONITORING_COCKROACHDB = "db-monitoring-cockroachdb"
    DB_MONITORING_QAN = "db-monitoring-qan"


class InsightType(StrEnum):
    """Telemetry insight types."""

    CHRONOLOGY = "chronology"
    PREDICTION = "prediction"
    RECOMMENDATION = "recommendation"
    ROOT_CAUSE = "root-cause"
    PATTERN = "pattern"


@dataclass(frozen=True, slots=True)
class TimeRange:
    """Time range value object."""

    from_time: datetime
    to_time: datetime

    def __post_init__(self) -> None:
        if self.from_time > self.to_time:
            raise ValueError("from_time must be before to_time")


@dataclass(frozen=True, slots=True)
class TelemetryContext:
    """Telemetry context value object mirroring TFO Platform TelemetryContext."""

    type: ContextType
    time_range: TimeRange
    summary: str
    data: Any
