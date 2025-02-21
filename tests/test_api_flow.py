#!/usr/bin/env python3
"""Run end-to-end tests for the LOACL API.

This script performs end-to-end testing of the LOACL API, including:
- User registration and authentication
- Assistant creation and management
- Real-time conversation testing
"""

import argparse
import json
import random
import sys
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests


class APITestFlow:
    """Test class for validating the LOACL API flow."""

    def __init__(self, base_url: str, assistant_id: str, openai_key: str):
        """Initialize the test flow.

        Args:
            base_url: Base URL of the API
            assistant_id: OpenAI Assistant ID
            openai_key: OpenAI API key
        """
        print("\nInitializing with:")
        print(f"Base URL: {base_url}")
        print(f"Assistant ID: {assistant_id}")
        # Mask the key
        print(f"OpenAI Key: {'*' * len(openai_key)}")

        self.base_url = base_url.rstrip("/")
        # OpenAI's assistant ID (asst_*)
        self.openai_assistant_id = assistant_id
        self.openai_key = openai_key
        self.access_token: Optional[str] = None
        # Local UUID for the assistant
        self.local_assistant_id: Optional[str] = None
        self.thread_id: Optional[str] = None
        self.headers: Dict[str, str] = {}

        # Generate a random ID for the test user
        self.random_id = random.randint(1000, 9999)
        self.test_email = f"ashaheen+loacl+{self.random_id}@workhub.ai"
        self.test_password = "uraan123"

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

            # Try to parse and format error response
            try:
                error_data = response.json()
                if isinstance(error_data, dict):
                    if "error" in error_data and isinstance(error_data["error"], dict):
                        # OpenAI style errors
                        error_type = error_data["error"].get("type", "unknown")
                        error_msg = error_data["error"].get("message", "No message")
                        print(f"Error type: {error_type}")
                        print(f"Error message: {error_msg}")
                    elif "detail" in error_data:
                        # FastAPI style errors
                        print(
                            f"Error details: {json.dumps(error_data['detail'], indent=2)}"
                        )
                    else:
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
        # Send as form data instead of JSON
        data = {
            "grant_type": "password",  # Required for OAuth2 password flow
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

    def create_assistant(self) -> Dict[str, Any]:
        """Create a new assistant.

        Returns:
            Assistant creation response
        """
        print("\n3. Creating assistant...")
        # Validate assistant_id format
        if not self.openai_assistant_id.startswith("asst_"):
            raise ValueError(
                f"Invalid assistant ID format. Got '{self.openai_assistant_id}' "
                "but it must start with 'asst_'"
            )

        print(
            f"Creating assistant with OpenAI Assistant ID: "
            f"{self.openai_assistant_id}"
        )
        data = {
            "name": "Test Assistant",
            "description": "A test assistant for API flow testing",
            "instructions": "You are a helpful test assistant",
            "model": "gpt-4-turbo-preview",
            "api_key": self.openai_key,
            "assistant_id": self.openai_assistant_id,
            "tools_enabled": ["code_interpreter"],
        }
        response = self._make_request("POST", "/api/v1/assistants", data)
        self.local_assistant_id = response["id"]
        print(f"Created local assistant with ID: {self.local_assistant_id}")
        return response

    def update_assistant_settings(self) -> Dict[str, Any]:
        """Update assistant settings.

        Returns:
            Settings update response
        """
        print("\n4. Updating assistant settings...")
        data = {
            "theme": {
                "primary_color": "#FF0000",
                "secondary_color": "#00FF00",
                "text_color": "#0000FF",
                "background_color": "#FFFFFF",
            },
            "chat_bubble_text": "Chat with me!",
            "initial_message": "Hello! How can I help you today!",
        }
        return self._make_request(
            "PUT", f"/api/v1/assistants/{self.local_assistant_id}", data
        )

    def get_widget_code(self) -> Dict[str, Any]:
        """Get widget embed code.

        Returns:
            Widget code response
        """
        print("\n5. Getting widget code...")
        return self._make_request(
            "GET", f"/api/v1/assistants/{self.local_assistant_id}/embed"
        )

    def get_widget_settings(self) -> Dict[str, Any]:
        """Get widget settings.

        Returns:
            Widget settings response
        """
        print("\n6. Getting widget settings...")
        return self._make_request(
            "GET", f"/api/v1/assistants/{self.local_assistant_id}"
        )

    def send_message(self, message: str) -> Optional[Dict[str, Any]]:
        """Send a message to the assistant and get the response.

        Args:
            message: Message content to send

        Returns:
            Assistant's response message or None if no response
        """
        print(f"\nSending message: {message}")
        # First create a thread
        if not self.thread_id:
            thread_data: Dict[str, Any] = {"messages": []}
            thread_response = self._make_request(
                "POST",
                "/api/v1/assistant-communication/threads",
                data=thread_data,
                params={"assistant_id": self.local_assistant_id},
            )
            self.thread_id = thread_response["id"]
            print(f"Created new thread with ID: {self.thread_id}")

        # Add message to thread
        message_data = {"content": message}
        _ = self._make_request(
            "POST",
            f"/api/v1/assistant-communication/threads/{self.thread_id}/messages",
            data=message_data,
            params={"assistant_id": self.local_assistant_id},
        )
        print("Message sent successfully")

        # Create and monitor run
        run_data: Dict[str, Any] = {
            "assistant_id": self.local_assistant_id,
            "instructions": None,
            "tools": [],
        }
        print(f"Creating run with local assistant ID: {self.local_assistant_id}")
        run_response = self._make_request(
            "POST",
            f"/api/v1/assistant-communication/threads/{self.thread_id}/runs",
            data=run_data,
        )

        # Poll for completion
        run_id = run_response["id"]
        print("Waiting for assistant's response...")
        while True:
            run_status = self._make_request(
                "GET",
                (
                    f"/api/v1/assistant-communication/threads/"
                    f"{self.thread_id}/runs/{run_id}"
                ),
                params={"assistant_id": self.local_assistant_id},
            )
            if run_status["status"] in ["completed", "failed"]:
                break
            time.sleep(1)
            print(".", end="", flush=True)
        print("\n")

        # Get messages
        messages = self._make_request(
            "GET",
            f"/api/v1/assistant-communication/threads/{self.thread_id}/messages",
            params={"assistant_id": self.local_assistant_id},
        )

        # Return the latest assistant message
        for msg in messages:
            if msg["role"] == "assistant":
                return msg
        return None

    def delete_assistant(self) -> Dict[str, Any]:
        """Delete the test assistant.

        Returns:
            Deletion response
        """
        print("\n9. Deleting assistant...")
        return self._make_request(
            "DELETE", f"/api/v1/assistants/{self.local_assistant_id}"
        )


def main() -> None:
    """Run the API test flow."""
    parser = argparse.ArgumentParser(description="Test LOACL API flow")
    parser.add_argument(
        "--base-url", default="http://localhost:8000", help="Base URL of the API"
    )
    parser.add_argument("--assistant-id", required=True, help="OpenAI Assistant ID")
    parser.add_argument("--openai-key", required=True, help="OpenAI API Key")
    args = parser.parse_args()

    test_flow = APITestFlow(args.base_url, args.assistant_id, args.openai_key)

    try:
        # Execute the test flow
        test_flow.register_user()
        test_flow.login_user()
        test_flow.create_assistant()
        test_flow.update_assistant_settings()
        widget_code = test_flow.get_widget_code()
        print("Widget Code:", json.dumps(widget_code, indent=2))
        settings = test_flow.get_widget_settings()
        print("Widget Settings:", json.dumps(settings, indent=2))

        print("\n=== Starting Conversation Test ===\n")

        # Test conversation with 5 back-and-forth exchanges
        conversations: List[Dict[str, str]] = [
            {
                "user": (
                    "Hello! I'm interested in learning about software testing "
                    "best practices. Can you help me understand the key "
                    "principles?"
                ),
                "context": "Initial question about testing principles",
            },
            {
                "user": (
                    "That's helpful! Could you elaborate specifically on the "
                    "difference between unit tests and integration tests, and "
                    "when to use each?"
                ),
                "context": "Follow-up on test types",
            },
            {
                "user": (
                    "Great explanation! Now, what are some popular Python "
                    "testing frameworks you'd recommend, and what makes them "
                    "stand out?"
                ),
                "context": "Question about testing tools",
            },
            {
                "user": (
                    "I've heard about test-driven development (TDD). Could you "
                    "explain its benefits and potential drawbacks?"
                ),
                "context": "Exploring TDD methodology",
            },
            {
                "user": (
                    "Finally, can you provide some best practices for writing "
                    "maintainable and readable test cases?"
                ),
                "context": "Best practices for test writing",
            },
        ]

        for i, conv in enumerate(conversations, 1):
            print(f"\n=== Exchange {i} ===")
            print(f"\nContext: {conv['context']}")
            print(f"\nUser: {conv['user']}")

            response = test_flow.send_message(conv["user"])
            if response:
                print(f"\nAssistant: {response['content']}")
            else:
                print("\nNo response from assistant")

            print("\n" + "=" * 50)

        # Cleanup
        test_flow.delete_assistant()
        print("\nTest flow completed successfully!")

    except Exception as e:
        print(f"\nError during test flow: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
