# tests/unit/test_register_unit.py

import pytest
import json
import boto3
from moto import mock_cognitoidp, mock_secretsmanager

from src.register import app

@pytest.fixture(scope="module")
def setup_register_env():
    region = "us-east-1"

    with mock_cognitoidp(), mock_secretsmanager():
        cognito = boto3.client("cognito-idp", region_name=region)
        secrets = boto3.client("secretsmanager", region_name=region)

        # Crear pool
        pool = cognito.create_user_pool(PoolName="RegisterPool")
        user_pool_id = pool["UserPool"]["Id"]

        # Crear secreto con pool ID
        secrets.create_secret(
            Name="userapp/env-variables",
            SecretString=json.dumps({
                "USER_POOL_ID": user_pool_id,
                "USER_POOL_CLIENT_ID": "fake"  # no se usa para register
            })
        )

        # Inyectar mocks
        app.cognito = cognito
        app.secrets_client = secrets

        yield cognito, user_pool_id

def test_register_success(setup_register_env):
    event = {
        "body": json.dumps({
            "email": "nuevo@ejemplo.com",
            "password": "Temp123!"
        })
    }

    response = app.lambda_handler(event, None)
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["message"] == "User registered"

def test_register_user_exists(setup_register_env):
    cognito, user_pool_id = setup_register_env

    # Crear usuario previamente
    cognito.admin_create_user(
        UserPoolId=user_pool_id,
        Username="repetido@ejemplo.com",
        TemporaryPassword="Temp123!",
        MessageAction="SUPPRESS"
    )

    event = {
        "body": json.dumps({
            "email": "repetido@ejemplo.com",
            "password": "OtraPass123"
        })
    }

    response = app.lambda_handler(event, None)
    assert response["statusCode"] == 409
    body = json.loads(response["body"])
    assert body["message"] == "User already exists"
