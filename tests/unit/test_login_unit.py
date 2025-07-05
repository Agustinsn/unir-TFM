# tests/unit/test_login_user.py
import os
import json
import boto3
import pytest
from src.login.app import lambda_handler

@pytest.fixture(autouse=True)
def cognito_mock():
    with mock_cognitoidp():
        client = boto3.client("cognito-idp", region_name="us-east-1")
        pool = client.create_user_pool(PoolName="test-pool")
        os.environ["USER_POOL_ID"] = pool["UserPool"]["Id"]
        client.create_user_pool_client(
            UserPoolId=pool["UserPool"]["Id"],
            ClientName="test-client",
            GenerateSecret=False
        )
        client.admin_create_user(
            UserPoolId=pool["UserPool"]["Id"],
            Username="juan",
            TemporaryPassword="Temp123!"
        )
        client.admin_set_user_password(
            UserPoolId=pool["UserPool"]["Id"],
            Username="juan",
            Password="Secreto123!",
            Permanent=True
        )
        yield

def test_login_success():
    event = {
        "body": json.dumps({
            "username": "juan",
            "password": "Secreto123!"
        })
    }
    resp = handler(event, None)
    body = json.loads(resp["body"])
    assert resp["statusCode"] == 200
    assert "AuthenticationResult" in body

def test_login_bad_password():
    event = {
        "body": json.dumps({
            "username": "juan",
            "password": "Wrong!"
        })
    }
    resp = handler(event, None)
    assert resp["statusCode"] == 401
