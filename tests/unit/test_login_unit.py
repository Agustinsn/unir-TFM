import json
import pytest
from moto import mock_cognitoidp, mock_secretsmanager
import boto3
import src.login.app as login_app

@pytest.fixture(scope="module")
def setup_environment():
    with mock_cognitoidp():
        with mock_secretsmanager():
            region = "us-east-1"
            cognito = boto3.client("cognito-idp", region_name=region)
            secrets = boto3.client("secretsmanager", region_name=region)

            # Crear user pool
            user_pool_id = cognito.create_user_pool(PoolName="test-pool")['UserPool']['Id']

            # Crear app client
            client_id = cognito.create_user_pool_client(
                UserPoolId=user_pool_id,
                ClientName="test-client",
                GenerateSecret=False,
                ExplicitAuthFlows=[
                    "ADMIN_NO_SRP_AUTH",
                    "ALLOW_ADMIN_USER_PASSWORD_AUTH"
                ]
            )['UserPoolClient']['ClientId']

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

            # Crear usuario NO confirmado
            cognito.admin_create_user(
                UserPoolId=user_pool_id,
                Username="unconfirmed@example.com",
                TemporaryPassword="TempPass123!",
                MessageAction="SUPPRESS"
            )
            # No se confirma intencionalmente

            # Crear secreto simulado
            secrets.create_secret(
                Name="userapp/env-variables",
                SecretString=json.dumps({
                    "USER_POOL_ID": user_pool_id,
                    "USER_POOL_CLIENT_ID": client_id
                })
            )

            return cognito, secrets, client_id


def test_login_success(setup_environment, monkeypatch):
    monkeypatch.setenv("USER_POOL_ID", setup_environment[0].list_user_pools(MaxResults=1)['UserPools'][0]['Id'])
    monkeypatch.setenv("USER_POOL_CLIENT_ID", setup_environment[2])

    event = {
        "body": json.dumps({
            "email": "test@example.com",
            "password": "Test123!"
        })
    }
    response = login_app.lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "access_token" in body


def test_login_invalid_password(setup_environment, monkeypatch):
    monkeypatch.setenv("USER_POOL_ID", setup_environment[0].list_user_pools(MaxResults=1)['UserPools'][0]['Id'])
    monkeypatch.setenv("USER_POOL_CLIENT_ID", setup_environment[2])

    event = {
        "body": json.dumps({
            "email": "test@example.com",
            "password": "WrongPassword!"
        })
    }
    response = login_app.lambda_handler(event, None)
    assert response["statusCode"] == 401


def test_login_unconfirmed_user(setup_environment, monkeypatch):
    monkeypatch.setenv("USER_POOL_ID", setup_environment[0].list_user_pools(MaxResults=1)['UserPools'][0]['Id'])
    monkeypatch.setenv("USER_POOL_CLIENT_ID", setup_environment[2])

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
