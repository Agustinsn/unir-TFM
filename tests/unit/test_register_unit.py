# tests/unit/test_register_unit.py

import pytest
import json
import boto3
from moto import mock_cognitoidp, mock_secretsmanager

from src.register import app  # Tu función lambda_handler ya refactorizada

@pytest.fixture(scope="module")
def setup_register_env():
    region = "us-east-1"

    with mock_cognitoidp(), mock_secretsmanager():
        cognito = boto3.client("cognito-idp", region_name=region)
        secrets = boto3.client("secretsmanager", region_name=region)

        # Crear user pool
        pool = cognito.create_user_pool(PoolName="TestPoolRegister")
        user_pool_id = pool["UserPool"]["Id"]

        # Crear user pool client
        client = cognito.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName="TestClientRegister"
        )
        client_id = client["UserPoolClient"]["ClientId"]

        # Guardar secreto con ID del pool y client
        secrets.create_secret(
            Name="userapp/env-variables",
            SecretString=json.dumps({
                "USER_POOL_ID": user_pool_id,
                "USER_POOL_CLIENT_ID": client_id
            })
        )

        yield cognito, secrets, client_id

def test_register_success(setup_register_env):
    cognito, secrets, client_id = setup_register_env

    event = {
        "body": json.dumps({
            "email": "nuevo@ejemplo.com",
            "password": "Temp123!"
        })
    }

    response = app.lambda_handler(event, None, cognito_client=cognito, secrets=secrets)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["message"] == "User registered successfully"

def test_register_user_exists(setup_register_env):
    cognito, secrets, client_id = setup_register_env

    # Crear previamente el usuario
    cognito.sign_up(
        ClientId=client_id,
        Username="existente@ejemplo.com",
        Password="Temp123!",
        UserAttributes=[{"Name": "email", "Value": "existente@ejemplo.com"}]
    )

    # Intentar registrar el mismo usuario
    event = {
        "body": json.dumps({
            "email": "existente@ejemplo.com",
            "password": "OtraPass123!"
        })
    }

    response = app.lambda_handler(event, None, cognito_client=cognito, secrets=secrets)
    assert response["statusCode"] == 409
    body = json.loads(response["body"])
    assert body["message"] == "User already exists"

def test_register_missing_fields(setup_register_env):
    cognito, secrets, _ = setup_register_env

    event = {
        "body": json.dumps({
            "email": "incompleto@ejemplo.com"
            # Falta la contraseña
        })
    }

    response = app.lambda_handler(event, None, cognito_client=cognito, secrets=secrets)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["message"] == "Email and password are required"
