import json
import pytest
from moto import mock_cognitoidp, mock_secretsmanager
import boto3
import os

import src.login.app as login_app
import src.register.app as register_app

USER_POOL_ID_ENV = "test_user_pool"
CLIENT_ID_ENV = "test_client_id"

@pytest.fixture(scope="function")
def setup_environment(monkeypatch):
    with mock_cognitoidp(), mock_secretsmanager():
        region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

        # Mock Cognito y SecretsManager
        cognito = boto3.client("cognito-idp", region_name=region)
        secrets = boto3.client("secretsmanager", region_name=region)

        # Crear User Pool
        user_pool = cognito.create_user_pool(PoolName=USER_POOL_ID_ENV)
        user_pool_id = user_pool["UserPool"]['Id']

        # Crear App Client
        client = cognito.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName=CLIENT_ID_ENV,
            GenerateSecret=False,
            ExplicitAuthFlows=[
                "ALLOW_ADMIN_USER_PASSWORD_AUTH",
                "ALLOW_USER_PASSWORD_AUTH",
                "ALLOW_REFRESH_TOKEN_AUTH"
            ]
        )
        client_id = client["UserPoolClient"]["ClientId"]

        # Mock secreto con IDs
        secrets.create_secret(
            Name="userapp/env-variables",
            SecretString=json.dumps({
                "USER_POOL_ID": user_pool_id,
                "USER_POOL_CLIENT_ID": client_id
            })
        )

        # Crear usuario confirmado
        cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username="test@example.com",
            TemporaryPassword="TempPass123!",
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

        monkeypatch.setenv("USER_POOL_ID", user_pool_id)
        monkeypatch.setenv("USER_POOL_CLIENT_ID", client_id)

        yield cognito, secrets, client_id

def test_login_success(setup_environment):
    event = {
        "body": json.dumps({
            "email": "test@example.com",
            "password": "Test123!"
        })
    }
    response = login_app.lambda_handler(event, None)
    assert response["statusCode"] == 200

def test_login_invalid_password(setup_environment):
    event = {
        "body": json.dumps({
            "email": "test@example.com",
            "password": "WrongPassword!"
        })
    }
    response = login_app.lambda_handler(event, None)
    assert response["statusCode"] == 401

def test_login_unconfirmed_user(setup_environment):
    event = {
        "body": json.dumps({
            "email": "unconfirmed@example.com",
            "password": "TempPass123!"
        })
    }
    response = login_app.lambda_handler(event, None)
    assert response["statusCode"] == 403

def test_register_success(setup_environment):
    _, _, client_id = setup_environment
    event = {
        "body": json.dumps({
            "email": "nuevo@ejemplo.com",
            "password": "Temp123!"
        })
    }
    response = register_app.lambda_handler(event, None)
    assert response["statusCode"] == 200

def test_register_user_exists(setup_environment):
    cognito, _, client_id = setup_environment

    # Crear usuario previamente
    cognito.sign_up(
        ClientId=client_id,
        Username="repetido@ejemplo.com",
        Password="Temp123!",
        UserAttributes=[{"Name": "email", "Value": "repetido@ejemplo.com"}]
    )

    event = {
        "body": json.dumps({
            "email": "repetido@ejemplo.com",
            "password": "OtraPass123"
        })
    }
    response = register_app.lambda_handler(event, None)
    assert response["statusCode"] == 409
