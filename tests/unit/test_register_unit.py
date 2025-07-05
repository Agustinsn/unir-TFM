# tests/unit/test_register_user.py
import os
import json
import boto3
import pytest
from moto import mock_cognitoidp
from src.register_user.app import handler

@pytest.fixture(autouse=True)
def cognito_mock():
    with mock_cognitoidp():
        client = boto3.client("cognito-idp", region_name="us-east-1")
        pool = client.create_user_pool(PoolName="test-pool")
        os.environ["USER_POOL_ID"] = pool["UserPool"]["Id"]
        client.create_user_pool_client(
            UserPoolId=pool["UserPool"]["Id"],
            ClientName="test-client"
        )
        yield

def test_register_success():
    event = {
        "body": json.dumps({
            "username": "juan",
            "password": "Secreto123!"
        })
    }
    resp = handler(event, None)
    body = json.loads(resp["body"])
    assert resp["statusCode"] == 201
    assert "User created" in body["message"]

def test_register_missing_fields():
    event = {"body": json.dumps({})}
    resp = handler(event, None)
    assert resp["statusCode"] == 400
