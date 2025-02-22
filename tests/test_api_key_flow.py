#!/usr/bin/env python3
"""Run end-to-end tests for the LOACL API Key functionality.

This script performs end-to-end testing of the LOACL API Key management, including:
- User registration and authentication
- API key creation and management
"""

import argparse
import json
import random
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests


class APIKeyTestFlow:
    """Test class for validating the API Key management flow."""

    def __init__(self, base_url: str):
        """Initialize the test flow.

        Args:
            base_url: Base URL of the API
        """
        print("\nInitializing with:")
        print(f"Base URL: {base_url}")

        self.base_url = base_url.rstrip("/")
        self.access_token: Optional[str] = None
        self.headers: Dict[str, str] = {}
        self.api_key_id: Optional[str] = None

        # Generate a random ID for the test user
        self.random_id = random.randint(1000, 9999)
        self.test_email = f"test.user+{self.random_id}@example.com"
        self.test_password = "testpass123"

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data
            params: Query parameters

        Returns:
            API response as dictionary
        """
        url = urljoin(self.base_url, endpoint)
        headers = self.headers.copy()

        if data and method != "GET":
            # Sanitize data for logging
            log_data = data.copy()
            if "api_key" in log_data:
                log_data["api_key"] = "***"
            print(f"Request data: {json.dumps(log_data, indent=2)}")

            headers["Content-Type"] = "application/json"
            response = requests.request(
                method, url, json=data, headers=headers, params=params
            )
        else:
            response = requests.request(method, url, headers=headers, params=params)

        try:
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.HTTPError as e:
            print(f"\nError in {method} {endpoint}:")
            print(f"Status code: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error response: {json.dumps(error_data, indent=2)}")
            except json.JSONDecodeError:
                print(f"Raw error response: {response.text}")
            raise e

    def register_user(self) -> Dict[str, Any]:
        """Register a new test user.

        Returns:
            Registration response
        """
        print("\n1. Registering user...")
        data = {
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Test User",
        }
        return self._make_request("POST", "/api/v1/auth/register", data)

    def login_user(self) -> Dict[str, Any]:
        """Log in the test user.

        Returns:
            Login response with access token
        """
        print("\n2. Logging in user...")
        data = {
            "grant_type": "password",
            "username": self.test_email,
            "password": self.test_password,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(
            urljoin(self.base_url, "/api/v1/auth/login/access-token"),
            data=data,
            headers=headers,
        )
        response.raise_for_status()
        response_data = response.json()
        self.access_token = response_data["access_token"]
        self.headers["Authorization"] = f"Bearer {self.access_token}"
        return response_data

    def create_api_key(self) -> Dict[str, Any]:
        """Create a new API key.

        Returns:
            API key creation response
        """
        print("\n3. Creating API key...")
        data = {"name": "Test API Key"}
        response = self._make_request("POST", "/api/v1/api-keys", data)
        self.api_key_id = response["id"]
        print(f"Created API key with ID: {self.api_key_id}")
        return response

    def list_api_keys(self) -> List[Dict[str, Any]]:
        """List all API keys.

        Returns:
            List of API keys
        """
        print("\n4. Listing API keys...")
        return self._make_request("GET", "/api/v1/api-keys")

    def get_api_key(self) -> Dict[str, Any]:
        """Get the created API key.

        Returns:
            API key details
        """
        print("\n5. Getting API key details...")
        return self._make_request("GET", f"/api/v1/api-keys/{self.api_key_id}")

    def delete_api_key(self) -> None:
        """Delete the created API key."""
        print("\n6. Deleting API key...")
        self._make_request("DELETE", f"/api/v1/api-keys/{self.api_key_id}")


def main() -> None:
    """Run the API key test flow."""
    parser = argparse.ArgumentParser(description="Test LOACL API Key Management")
    parser.add_argument(
        "--base-url", default="http://localhost:8000", help="Base URL of the API"
    )
    args = parser.parse_args()

    test_flow = APIKeyTestFlow(args.base_url)

    try:
        # Execute the test flow
        print("\n=== Starting API Key Management Test ===\n")

        # User registration and authentication
        test_flow.register_user()
        test_flow.login_user()

        # API key management
        created_key = test_flow.create_api_key()
        print("\nCreated API Key:")
        print(json.dumps(created_key, indent=2))

        # List all keys
        api_keys = test_flow.list_api_keys()
        print(f"\nFound {len(api_keys)} API key(s)")

        # Get specific key
        key_details = test_flow.get_api_key()
        print("\nAPI Key Details:")
        print(json.dumps(key_details, indent=2))

        # Delete key
        test_flow.delete_api_key()
        print("\nAPI key deleted successfully")

        # Verify deletion
        try:
            test_flow.get_api_key()
            print("ERROR: API key still exists after deletion!")
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print("✓ API key successfully deleted (404 Not Found)")
            else:
                raise

        print("\nTest flow completed successfully!")

    except Exception as e:
        print(f"\nError during test flow: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
