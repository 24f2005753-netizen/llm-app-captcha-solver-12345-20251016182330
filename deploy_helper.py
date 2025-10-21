"""
Deploy Helper Module for communicating with evaluation APIs
"""

import os
import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeployHelper:
    def __init__(self):
        self.timeout = 30.0  # 30 second timeout for HTTP requests
    
    async def notify_evaluation_api(self, 
                                  evaluation_url: str,
                                  email: str,
                                  task: str,
                                  round_num: int,
                                  nonce: str,
                                  repo_data: Dict[str, Any],
                                  app_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send deployment metadata to the evaluation API
        """
        try:
            # Prepare the payload
            payload = {
                "email": email,
                "task": task,
                "round": round_num,
                "nonce": nonce,
                "timestamp": datetime.utcnow().isoformat(),
                "deployment": {
                    "repo_name": repo_data.get("repo_name"),
                    "repo_url": repo_data.get("repo_url"),
                    "commit_sha": repo_data.get("commit_sha"),
                    "pages_url": repo_data.get("pages_url"),
                    "success": repo_data.get("success", False)
                },
                "app_metadata": app_metadata
            }
            
            logger.info(f"Sending evaluation notification to: {evaluation_url}")
            logger.info(f"Payload: {json.dumps(payload, indent=2)}")
            
            # Send the request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    evaluation_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "LLM-Code-Deployment/1.0"
                    }
                )
                
                # Log the response
                logger.info(f"Evaluation API response status: {response.status_code}")
                logger.info(f"Evaluation API response: {response.text}")
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                    }
                else:
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": f"Evaluation API returned status {response.status_code}: {response.text}"
                    }
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout while calling evaluation API: {evaluation_url}")
            return {
                "success": False,
                "error": "Request timeout"
            }
        except httpx.RequestError as e:
            logger.error(f"Request error while calling evaluation API: {e}")
            return {
                "success": False,
                "error": f"Request error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error while calling evaluation API: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def validate_evaluation_url(self, url: str) -> bool:
        """
        Basic validation of evaluation URL
        """
        try:
            if not url or not isinstance(url, str):
                return False
            
            # Check if it's a valid HTTP/HTTPS URL
            if not (url.startswith("http://") or url.startswith("https://")):
                return False
            
            # Basic URL structure validation
            if "." not in url.replace("://", ""):
                return False
            
            return True
            
        except Exception:
            return False
    
    def format_deployment_summary(self, 
                                repo_data: Dict[str, Any], 
                                app_metadata: Dict[str, Any]) -> str:
        """
        Format a human-readable deployment summary
        """
        summary = f"""
🚀 Deployment Summary
====================

Repository: {repo_data.get('repo_name', 'N/A')}
Repository URL: {repo_data.get('repo_url', 'N/A')}
GitHub Pages: {repo_data.get('pages_url', 'N/A')}
Commit SHA: {repo_data.get('commit_sha', 'N/A')[:8]}...
Status: {'✅ Success' if repo_data.get('success') else '❌ Failed'}

App Metadata:
- Title: {app_metadata.get('title', 'N/A')}
- Description: {app_metadata.get('description', 'N/A')}
- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        return summary.strip()
