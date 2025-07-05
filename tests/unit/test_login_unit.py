# tests/unit/test_login_unit.py

import pytest
from moto import mock_cognitoidp
import boto3
from src.login import app

@pytest.fixture(autouse=True)
def mock_cognito():
    with mock_cognitoidp():
        client = boto3.client("cognito-idp", region_name="us-east-1")

        # Crear UserPool
        user_pool = client.create_user_pool(PoolName="TestPool")
        user_pool_id = user_pool["UserPool"]["Id"]

        # Crear UserPoolClient
        user_pool_client = client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName="TestClient"
        )
        client_id = user_pool_client["UserPoolClient"]["ClientId"]

        email = "test@example.com"
        password = "Test123!"
        client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            TemporaryPassword=password,
            MessageAction='SUPPRESS'
        )
        client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=password,
            Permanent=True
        )

        app.client = client
        app.COGNITO_CLIENT_ID = client_id
        app.COGNITO_USER_POOL_ID = user_pool_id

        yield

def test_login_success():
    event = {
        "body": {
            "email": "test@example.com",
            "password": "Test123!"
        }
    }

    response = app.lambda_handler(event, None)
    assert response["statusCode"] == 200
    assert "access_token" in response["body"]

def test_login_invalid_password():
    event = {
        "body": {
            "email": "test@example.com",
            "password": "WrongPass!"
        }
    }

    response = app.lambda_handler(event, None)
    assert response["statusCode"] == 401
    assert response["body"] == "Incorrect username or password"

def test_login_user_not_found():
    event = {
        "body": {
            "email": "noexist@example.com",
            "password": "Whatever123"
        }
    }

    response = app.lambda_handler(event, None)
    assert response["statusCode"] == 404
    assert response["body"] == "User not found"
