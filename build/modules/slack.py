#!/usr/bin/env python3
"""
Slack notification module for Nxtscape build system
"""

import os
import json
import requests
from typing import Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import log_info, log_warning, log_error


def get_slack_webhook_url() -> Optional[str]:
    """Get Slack webhook URL from environment variable"""
    return os.environ.get("SLACK_WEBHOOK_URL")


def send_slack_notification(message: str, success: bool = True) -> bool:
    """Send a notification to Slack if webhook URL is configured"""
    webhook_url = get_slack_webhook_url()
    
    if not webhook_url:
        # Silently skip if no webhook configured
        return True
    
    # Choose emoji and color based on success status
    emoji = "✅" if success else "❌"
    color = "good" if success else "danger"
    
    # Create Slack message payload
    payload = {
        "attachments": [
            {
                "color": color,
                "fields": [
                    {
                        "title": "Nxtscape Build",
                        "value": f"{emoji} {message}",
                        "short": False
                    }
                ],
                "footer": "Nxtscape Build System",
                "ts": None  # Slack will use current timestamp
            }
        ]
    }
    
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            log_info(f"📲 Slack notification sent: {message}")
            return True
        else:
            log_warning(f"Slack notification failed with status {response.status_code}")
            return False
            
    except requests.RequestException as e:
        log_warning(f"Failed to send Slack notification: {e}")
        return False


def notify_build_started(build_type: str, arch: str) -> bool:
    """Notify that build has started"""
    message = f"Build started - {build_type} build for {arch}"
    return send_slack_notification(message, success=True)


def notify_build_step(step_name: str) -> bool:
    """Notify about a build step"""
    message = f"Running step: {step_name}"
    return send_slack_notification(message, success=True)


def notify_build_success(duration_mins: int, duration_secs: int) -> bool:
    """Notify that build completed successfully"""
    message = f"Build completed successfully in {duration_mins}m {duration_secs}s"
    return send_slack_notification(message, success=True)


def notify_build_failure(error_message: str) -> bool:
    """Notify that build failed"""
    message = f"Build failed: {error_message}"
    return send_slack_notification(message, success=False)


def notify_build_interrupted() -> bool:
    """Notify that build was interrupted"""
    message = "Build was interrupted by user"
    return send_slack_notification(message, success=False)
