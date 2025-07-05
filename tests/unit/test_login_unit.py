# tests/unit/test_login_unit.py

import pytest
import json
import boto3
from moto import mock_cognitoidp, mock_secretsmanager

from src.login import app

@pytest.fixture(scope="module")
def setup_environment():
    region = "us-east-1"

    with mock_cognitoidp(), mock_secretsmanager():
        cognito = boto3.client("cognito-idp", region_name=region)
        secrets = boto3.client("secretsmanager", region_name=region)

        # Crear user pool
        pool = cognito.create_user_pool(PoolName="TestPool")
        user_pool_id = pool["UserPool"]["Id"]

        # Crear client
        client = cognito.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName="TestClient"
        )
        client_id = client["UserPoolClient"]["ClientId"]

        # Crear usuario confirmado
        cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username="test@example.com",
            TemporaryPassword="Test123!",
            MessageAction="SUPPRESS"
        )
        cognito.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username="test@example.com",
            Password="Test123!",
            Permanent=True
        )

        # Crear usuario no confirmado
        cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username="unconfirmed@example.com",
            TemporaryPassword="TempPass123!",
            MessageAction="SUPPRESS"
        )
        # (No llamamos a `admin_set_user_password`, queda no confirmado)

        # Crear secreto
        secrets.create_secret(
            Name="userapp/env-variables",
            SecretString=json.dumps({
                "USER_POOL_ID": user_pool_id,
                "USER_POOL_CLIENT_ID": client_id
            })
        )

        # Inyectar mocks
        app.cognito = cognito
        app.secrets_client = secrets

        yield

def test_login_success(setup_environment):
    event = {
        "body": json.dumps({
            "email": "test@example.com",
            "password": "Test123!"
        })
    }
    response = app.lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "access_token" in body

def test_login_invalid_password(setup_environment):
    event = {
        "body": json.dumps({
            "email": "test@example.com",
            "password": "WrongPassword!"
        })
    }
    response = app.lambda_handler(event, None)
    assert response["statusCode"] == 401
    body = json.loads(response["body"])
    assert body["message"] == "Invalid email or password"

def test_login_unconfirmed_user(setup_environment):
    event = {
        "body": json.dumps({
            "email": "unconfirmed@example.com",
            "password": "TempPass123!"
        })
    }
    response = app.lambda_handler(event, None)
    assert response["statusCode"] == 403
    body = json.loads(response["body"])
    assert body["message"] == "User not confirmed"
