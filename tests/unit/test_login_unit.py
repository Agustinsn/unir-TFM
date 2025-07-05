import json
import pytest
import boto3
from moto import mock_cognitoidp, mock_secretsmanager
import login_app  # tu archivo con lambda_handler

USER_POOL_ID = None
CLIENT_ID = None
SECRET_ARN = None

@pytest.fixture(scope="module")
def setup_environment():
    global USER_POOL_ID, CLIENT_ID, SECRET_ARN

    with mock_cognitoidp(), mock_secretsmanager():
        cognito_client = boto3.client("cognito-idp", region_name="us-east-1")
        secrets_client = boto3.client("secretsmanager", region_name="us-east-1")

        # Crear User Pool
        pool = cognito_client.create_user_pool(PoolName="test-pool")
        USER_POOL_ID = pool["UserPool"]["Id"]

        # Crear User Pool Client
        client = cognito_client.create_user_pool_client(
            UserPoolId=USER_POOL_ID,
            ClientName="test-client",
            GenerateSecret=False
        )
        CLIENT_ID = client["UserPoolClient"]["ClientId"]

        # Crear usuario confirmado
        cognito_client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username="user@example.com",
            TemporaryPassword="TempPass123!",
            UserAttributes=[
                {"Name": "email", "Value": "user@example.com"},
                {"Name": "email_verified", "Value": "true"}
            ],
            MessageAction="SUPPRESS"
        )
        cognito_client.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username="user@example.com",
            Password="TempPass123!",
            Permanent=True
        )

        # Crear usuario no confirmado
        cognito_client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username="unconfirmed@example.com",
            TemporaryPassword="TempPass123!",
            UserAttributes=[
                {"Name": "email", "Value": "unconfirmed@example.com"},
                {"Name": "email_verified", "Value": "true"}
            ],
            MessageAction="SUPPRESS"
        )

        # Guardar credenciales en Secrets Manager
        secret_value = json.dumps({
            "USER_POOL_ID": USER_POOL_ID,
            "USER_POOL_CLIENT_ID": CLIENT_ID
        })

        secret = secrets_client.create_secret(
            Name="userapp/env-variables",
            SecretString=secret_value
        )
        SECRET_ARN = secret["ARN"]

        yield (cognito_client, secrets_client, USER_POOL_ID)


def test_login_success(setup_environment, monkeypatch):
    monkeypatch.setenv("STAGE", "test")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    event = {
        "body": json.dumps({
            "email": "user@example.com",
            "password": "TempPass123!"
        })
    }
    response = login_app.lambda_handler(event, None)
    assert response["statusCode"] == 200


def test_login_invalid_password(setup_environment, monkeypatch):
    monkeypatch.setenv("STAGE", "test")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    event = {
        "body": json.dumps({
            "email": "user@example.com",
            "password": "WrongPass123"
        })
    }
    response = login_app.lambda_handler(event, None)
    assert response["statusCode"] == 401


def test_login_unconfirmed_user(setup_environment, monkeypatch):
    monkeypatch.setenv("STAGE", "test")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    event = {
        "body": json.dumps({
            "email": "unconfirmed@example.com",
            "password": "TempPass123!"
        })
    }
    response = login_app.lambda_handler(event, None)
    assert response["statusCode"] == 403


def test_invalid_json():
    event = {"body": "{malformed json]"}
    response = login_app.lambda_handler(event, None)
    assert response["statusCode"] == 400


def test_missing_credentials():
    event = {"body": json.dumps({})}
    response = login_app.lambda_handler(event, None)
    assert response["statusCode"] == 400
