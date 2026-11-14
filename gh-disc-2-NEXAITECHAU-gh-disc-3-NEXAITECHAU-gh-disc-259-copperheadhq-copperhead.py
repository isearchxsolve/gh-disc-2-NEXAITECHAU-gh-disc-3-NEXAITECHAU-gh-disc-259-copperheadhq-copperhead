import pytest
import requests
from requests_mock import Mocker
from datetime import datetime
import hmac
import hashlib
import json

# Simulated NEX Agent client (simplified for testing)
class NEXAgent:
    def __init__(self, api_key: str, secret_key: str, base_url: str = "https://api.nex-agent.com"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url

    def _sign_request(self, method: str, path: str, body: str = "") -> str:
        timestamp = str(int(datetime.utcnow().timestamp()))
        message = f"{method}\n{path}\n{timestamp}\n{body}"
        signature = hmac.new(
            self.secret_key.encode(), 
            message.encode(), 
            hashlib.sha256
        ).hexdigest()
        return f"HMAC {self.api_key}:{timestamp}:{signature}"

    def submit_transaction(self, payload: dict) -> dict:
        path = "/v1/transactions"
        body = json.dumps(payload, separators=(',', ':'))
        signature = self._sign_request("POST", path, body)
        headers = {
            "Content-Type": "application/json",
            "Authorization": signature
        }
        response = requests.post(f"{self.base_url}{path}", data=body, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

# Tests
@pytest.fixture
def mock_server():
    with Mocker() as m:
        yield m

def test_agent_initialization():
    agent = NEXAgent(api_key = "dummy_placeholder_secret", secret_key="test_secret")
    assert agent.api_key == "test_key"
    assert agent.secret_key == "test_secret"
    assert agent.base_url == "https://api.nex-agent.com"

def test_submit_transaction_success(mock_server):
    agent = NEXAgent(api_key = "dummy_placeholder_secret", secret_key="test_secret")
    expected_response = {"status": "success", "tx_id": "tx_12345"}
    
    # Mock the expected request
    mock_server.post(
        "https://api.nex-agent.com/v1/transactions",
        json=expected_response,
        status_code=200
    )
    
    result = agent.submit_transaction({"amount": 100, "currency": "USD"})
    assert result == expected_response

def test_submit_transaction_error_handling(mock_server):
    agent = NEXAgent(api_key = "dummy_placeholder_secret", secret_key="test_secret")
    
    mock_server.post(
        "https://api.nex-agent.com/v1/transactions",
        json={"error": "insufficient_funds"},
        status_code=400
    )
    
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        agent.submit_transaction({"amount": 100, "currency": "USD"})
    assert exc_info.value.response.status_code == 400

def test_sign_request_signature_format():
    agent = NEXAgent(api_key = "dummy_placeholder_secret", secret_key="test_secret")
    signature = agent._sign_request("POST", "/v1/transactions")
    parts = signature.split()
    assert len(parts) == 2
    assert parts[0] == "HMAC"
    assert len(parts[1].split(":")) == 3