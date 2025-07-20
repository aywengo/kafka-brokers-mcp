"""Utility functions for tests."""
import subprocess
import shutil


def get_docker_compose_cmd():
    """
    Determine which docker compose command to use.
    
    Returns:
        list: Command parts for docker compose (e.g., ['docker', 'compose'] or ['docker-compose'])
    
    Raises:
        RuntimeError: If neither docker compose command is available
    """
    # Try Docker Compose V2 (docker compose)
    try:
        result = subprocess.run(['docker', 'compose', 'version'], 
                              capture_output=True, check=True)
        return ['docker', 'compose']
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Try Docker Compose V1 (docker-compose)
    if shutil.which('docker-compose'):
        try:
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, check=True)
            return ['docker-compose']
        except subprocess.CalledProcessError:
            pass
    
    raise RuntimeError("Neither 'docker compose' nor 'docker-compose' is available")


def run_docker_compose(args, **kwargs):
    """
    Run a docker compose command with auto-detection of the right command.
    
    Args:
        args: Arguments to pass to docker compose (after the base command)
        **kwargs: Additional arguments to pass to subprocess.run()
    
    Returns:
        subprocess.CompletedProcess: Result of the subprocess.run() call
    """
    cmd = get_docker_compose_cmd()
    full_cmd = cmd + args
    return subprocess.run(full_cmd, **kwargs) 