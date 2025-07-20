#!/usr/bin/env python3
"""
Test runner that properly sets up environment variables before importing the main module.
This solves the import-time vs test-time environment variable issue.
"""

import os
import sys
import subprocess

def setup_test_environment():
    """Set up environment variables for testing."""
    # Set up basic Kafka cluster configuration that will allow module import
    test_env = {
        'KAFKA_BOOTSTRAP_SERVERS': 'localhost:9092',
        'KAFKA_SECURITY_PROTOCOL': 'PLAINTEXT', 
        'READONLY': 'false',
        
        # Multi-cluster configuration for comprehensive tests
        'KAFKA_CLUSTER_NAME_1': 'dev',
        'KAFKA_BOOTSTRAP_SERVERS_1': 'localhost:9092',
        'KAFKA_SECURITY_PROTOCOL_1': 'PLAINTEXT',
        'READONLY_1': 'false',
        
        'KAFKA_CLUSTER_NAME_2': 'prod', 
        'KAFKA_BOOTSTRAP_SERVERS_2': 'localhost:39093',
        'KAFKA_SECURITY_PROTOCOL_2': 'PLAINTEXT',
        'READONLY_2': 'false'
    }
    
    for key, value in test_env.items():
        os.environ[key] = value

if __name__ == "__main__":
    # Set up environment before any imports
    setup_test_environment()
    
    # Now we can safely run pytest
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        cmd = ["python3", "-m", "pytest", "-v", test_file]
    else:
        cmd = ["python3", "-m", "pytest", "-v"]
    
    # Run the test
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    sys.exit(result.returncode) 