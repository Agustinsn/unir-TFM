# tests/unit/test_register_unit.py

import pytest
from moto import mock_cognitoidp
import boto3
import os
import json

from src.register import app

@pytest.fixture(autouse=True)
def mock_cognito():
    with mock_cognitoidp():
        client = boto3.client("cognito-idp", region_name="us-east-1")
        user_pool = client.create_user_pool(PoolName="TestPool")
        user_pool_id = user_pool["UserPool"]["Id"]

        app.client = client
        app.COGNITO_CLIENT_ID = client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName="TestClient"
        )["UserPoolClient"]["ClientId"]

        yield

def test_register_success():
    event = {
        "body": json.dumps({
            "email": "test@example.com",
            "password": "Test123!"
        })
    }

    response = app.lambda_handler(event, None)
    assert response["statusCode"] == 201
    assert "userSub" in response["body"]

def test_register_user_exists():
    email = "test@example.com"
    password = "Test123!"

    event = {"body": json.dumps({"email": email, "password": password})}
    app.lambda_handler(event, None) 

    response = app.lambda_handler(event, None) 
    assert response["statusCode"] == 409
    assert response["body"] == "User already exists"
