#!/usr/bin/env python3
"""
Simple health check script for Docker containers using requests.
This script makes an HTTP request to the health endpoint.
"""

import sys
import requests

def health_check(url: str = "http://localhost:8000/health", timeout: int = 10) -> bool:
    """
    Perform a health check by making an HTTP request to the health endpoint.
    
    Args:
        url: The health check endpoint URL
        timeout: Request timeout in seconds
        
    Returns:
        True if healthy, False otherwise
    """
    try:
        # Make the request with requests library
        response = requests.get(
            url, 
            timeout=timeout,
            headers={'User-Agent': 'Docker-HealthCheck/1.0'}
        )
        
        # Check status code
        response.raise_for_status()  # Raises an exception for 4xx/5xx status codes
        
        # Parse JSON response
        data = response.json()
        status = data.get('status', '').lower()
        
        if status == 'healthy':
            print("Health check passed: Service is healthy")
            return True
        else:
            print(f"Health check failed: Status is '{status}'", file=sys.stderr)
            return False
        
    except Exception as e:
        print(f"Health check failed: Unexpected error - {e}", file=sys.stderr)
        return False

def main():
    """Main entry point for the health check script."""
    
    # Health check URL
    health_url = "http://localhost:8000/health"
    
    # Perform the health check
    if health_check(health_url):
        # Healthy - exit with code 0
        sys.exit(0)
    else:
        # Unhealthy - exit with code 1
        sys.exit(1)

if __name__ == "__main__":
    main()