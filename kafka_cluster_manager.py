"""
Kafka Cluster Management Module
Handles cluster configuration, connections, and AdminClient management.
"""

import logging
import os
from typing import Dict, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from confluent_kafka.admin import AdminClient

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class KafkaClusterConfig:
    """Configuration for a Kafka cluster connection."""

    name: str
    bootstrap_servers: str
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    ssl_ca_location: Optional[str] = None
    ssl_certificate_location: Optional[str] = None
    ssl_key_location: Optional[str] = None
    viewonly: bool = False


class KafkaClusterManager:
    """Manages Kafka cluster connections and operations."""

    def __init__(self):
        self.clusters: Dict[str, KafkaClusterConfig] = {}
        self.admin_clients: Dict[str, AdminClient] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)

    def add_cluster(self, config: KafkaClusterConfig):
        """Add a cluster configuration."""
        self.clusters[config.name] = config
        self._create_admin_client(config)

    def _create_admin_client(self, config: KafkaClusterConfig):
        """Create an AdminClient for the cluster."""
        kafka_config = {
            "bootstrap.servers": config.bootstrap_servers,
            "security.protocol": config.security_protocol,
        }

        if config.sasl_mechanism:
            kafka_config["sasl.mechanism"] = config.sasl_mechanism
        if config.sasl_username:
            kafka_config["sasl.username"] = config.sasl_username
        if config.sasl_password:
            kafka_config["sasl.password"] = config.sasl_password
        if config.ssl_ca_location:
            kafka_config["ssl.ca.location"] = config.ssl_ca_location
        if config.ssl_certificate_location:
            kafka_config["ssl.certificate.location"] = config.ssl_certificate_location
        if config.ssl_key_location:
            kafka_config["ssl.key.location"] = config.ssl_key_location

        self.admin_clients[config.name] = AdminClient(kafka_config)

    def get_admin_client(self, cluster_name: Optional[str] = None) -> AdminClient:
        """Get AdminClient for specified cluster or default."""
        if cluster_name is None:
            if len(self.admin_clients) == 1:
                return list(self.admin_clients.values())[0]
            elif "default" in self.admin_clients:
                return self.admin_clients["default"]
            else:
                raise ValueError("Multiple clusters available, please specify cluster_name")

        if cluster_name not in self.admin_clients:
            raise ValueError(f"Cluster '{cluster_name}' not found")

        return self.admin_clients[cluster_name]

    def get_cluster_config(self, cluster_name: Optional[str] = None) -> KafkaClusterConfig:
        """Get cluster configuration."""
        if cluster_name is None:
            if len(self.clusters) == 1:
                return list(self.clusters.values())[0]
            elif "default" in self.clusters:
                return self.clusters["default"]
            else:
                raise ValueError("Multiple clusters available, please specify cluster_name")

        if cluster_name not in self.clusters:
            raise ValueError(f"Cluster '{cluster_name}' not found")

        return self.clusters[cluster_name]

    def is_viewonly(self, cluster_name: Optional[str] = None) -> bool:
        """Check if cluster is in viewonly mode."""
        config = self.get_cluster_config(cluster_name)
        return config.viewonly


def load_cluster_configurations() -> KafkaClusterManager:
    """Load cluster configurations from environment variables."""
    manager = KafkaClusterManager()

    # Check for single cluster mode first
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    if bootstrap_servers:
        config = KafkaClusterConfig(
            name="default",
            bootstrap_servers=bootstrap_servers,
            security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
            sasl_username=os.getenv("KAFKA_SASL_USERNAME"),
            sasl_password=os.getenv("KAFKA_SASL_PASSWORD"),
            ssl_ca_location=os.getenv("KAFKA_SSL_CA_LOCATION"),
            ssl_certificate_location=os.getenv("KAFKA_SSL_CERTIFICATE_LOCATION"),
            ssl_key_location=os.getenv("KAFKA_SSL_KEY_LOCATION"),
            viewonly=os.getenv("VIEWONLY", "false").lower() == "true",
        )
        manager.add_cluster(config)
        logger.info(f"Loaded single cluster configuration: {bootstrap_servers}")
        return manager

    # Check for multi-cluster mode
    for i in range(1, 9):  # Support up to 8 clusters
        name = os.getenv(f"KAFKA_CLUSTER_NAME_{i}")
        servers = os.getenv(f"KAFKA_BOOTSTRAP_SERVERS_{i}")

        if name and servers:
            config = KafkaClusterConfig(
                name=name,
                bootstrap_servers=servers,
                security_protocol=os.getenv(f"KAFKA_SECURITY_PROTOCOL_{i}", "PLAINTEXT"),
                sasl_mechanism=os.getenv(f"KAFKA_SASL_MECHANISM_{i}"),
                sasl_username=os.getenv(f"KAFKA_SASL_USERNAME_{i}"),
                sasl_password=os.getenv(f"KAFKA_SASL_PASSWORD_{i}"),
                ssl_ca_location=os.getenv(f"KAFKA_SSL_CA_LOCATION_{i}"),
                ssl_certificate_location=os.getenv(f"KAFKA_SSL_CERTIFICATE_LOCATION_{i}"),
                ssl_key_location=os.getenv(f"KAFKA_SSL_KEY_LOCATION_{i}"),
                viewonly=os.getenv(f"VIEWONLY_{i}", "false").lower() == "true",
            )
            manager.add_cluster(config)
            logger.info(f"Loaded cluster configuration: {name} -> {servers}")

    if not manager.clusters:
        raise ValueError(
            "No cluster configurations found. Set KAFKA_BOOTSTRAP_SERVERS or KAFKA_CLUSTER_NAME_X/KAFKA_BOOTSTRAP_SERVERS_X"
        )

    return manager
