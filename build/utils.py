#!/usr/bin/env python3
"""
Shared utilities for the build system
"""

import os
import sys
import subprocess
import yaml
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime


# Global log file handle
_log_file = None


def _ensure_log_file():
    """Ensure log file is created with timestamp"""
    global _log_file
    if _log_file is None:
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file_path = log_dir / f"build_{timestamp}.log"
        _log_file = open(log_file_path, 'w')
        _log_file.write(f"Nxtscape Build Log - Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        _log_file.write("=" * 80 + "\n\n")
    return _log_file


def _log_to_file(message: str):
    """Write message to log file with timestamp"""
    log_file = _ensure_log_file()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file.write(f"[{timestamp}] {message}\n")
    log_file.flush()


def log_info(message: str):
    """Print info message"""
    print(message)
    _log_to_file(f"INFO: {message}")

def log_warning(message: str):
    """Print warning message"""
    print(f"⚠️ {message}")
    _log_to_file(f"WARNING: {message}")

def log_error(message: str):
    """Print error message"""
    print(f"❌ {message}")
    _log_to_file(f"ERROR: {message}")


def log_success(message: str):
    """Print success message"""
    print(f"✅ {message}")
    _log_to_file(f"SUCCESS: {message}")


def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    env: Optional[Dict] = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a command with real-time streaming output and full capture"""
    cmd_str = " ".join(cmd)
    _log_to_file(f"RUN_COMMAND: 🔧 Running: {cmd_str}")
    log_info(f"🔧 Running: {cmd_str}")

    try:
        # Always use Popen for real-time streaming and capturing
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env or os.environ,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        stdout_lines = []
        
        # Stream output line by line
        for line in iter(process.stdout.readline, ''):
            line = line.rstrip()
            if line:
                print(line)  # Print to console in real-time
                _log_to_file(f"RUN_COMMAND: STDOUT: {line}")  # Log to file
                stdout_lines.append(line)
        
        # Wait for process to complete
        process.wait()
        
        _log_to_file(f"RUN_COMMAND: ✅ Command completed with exit code: {process.returncode}")
        
        # Create a CompletedProcess object with captured output
        result = subprocess.CompletedProcess(
            cmd,
            process.returncode,
            stdout='\n'.join(stdout_lines) if stdout_lines else '',
            stderr=''
        )
        
        if check and process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd, result.stdout, result.stderr)
        
        return result
            
    except subprocess.CalledProcessError as e:
        _log_to_file(f"RUN_COMMAND: ❌ Command failed: {cmd_str}")
        _log_to_file(f"RUN_COMMAND: ❌ Exit code: {e.returncode}")
        
        if e.stdout:
            for line in e.stdout.strip().split('\n'):
                if line.strip():
                    _log_to_file(f"RUN_COMMAND: STDOUT: {line}")
        
        if e.stderr:
            for line in e.stderr.strip().split('\n'):
                if line.strip():
                    _log_to_file(f"RUN_COMMAND: STDERR: {line}")
        
        if check:
            log_error(f"Command failed: {cmd_str}")
            if e.stderr:
                log_error(f"Error: {e.stderr}")
            raise
        return e
    except Exception as e:
        _log_to_file(f"RUN_COMMAND: ❌ Unexpected error: {str(e)}")
        if check:
            log_error(f"Unexpected error running command: {cmd_str}")
            log_error(f"Error: {str(e)}")
        raise


def load_config(config_path: Path) -> Dict:
    """Load configuration from YAML file"""
    if not config_path.exists():
        log_error(f"Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config

