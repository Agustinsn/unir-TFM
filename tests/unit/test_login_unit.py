import json
import pytest
import login.app as login_app
from moto import mock_cognitoidp, mock_secretsmanager
import boto3

USER_EMAIL = "test@example.com"
USER_PASSWORD = "TempPass123!"
UNCONFIRMED_EMAIL = "unconfirmed@example.com"
INVALID_PASSWORD = "WrongPass123!"

@pytest.fixture(scope="module")
def setup_environment():
    with mock_cognitoidp():
        with mock_secretsmanager():
            region = "us-east-1"
            boto3.setup_default_session(region_name=region)

            cognito = boto3.client("cognito-idp", region_name=region)
            secrets = boto3.client("secretsmanager", region_name=region)

            user_pool_id = cognito.create_user_pool(PoolName="TestPool")['UserPool']['Id']

            client_id = cognito.create_user_pool_client(
                UserPoolId=user_pool_id,
                ClientName="TestClient",
                GenerateSecret=False
            )['UserPoolClient']['ClientId']

            # Crear secreto con credenciales
            secrets.create_secret(
                Name="userapp/env-variables",
                SecretString=json.dumps({
                    "USER_POOL_ID": user_pool_id,
                    "USER_POOL_CLIENT_ID": client_id
                })
            )

            # Crear usuario confirmado
            cognito.sign_up(
                ClientId=client_id,
                Username=USER_EMAIL,
                Password=USER_PASSWORD,
                UserAttributes=[{"Name": "email", "Value": USER_EMAIL}]
            )
            cognito.admin_confirm_sign_up(
                UserPoolId=user_pool_id,
                Username=USER_EMAIL
            )

            # Crear usuario no confirmado
            cognito.sign_up(
                ClientId=client_id,
                Username=UNCONFIRMED_EMAIL,
                Password=USER_PASSWORD,
                UserAttributes=[{"Name": "email", "Value": UNCONFIRMED_EMAIL}]
            )

            return cognito, secrets, client_id

def test_login_success(setup_environment, monkeypatch):
    monkeypatch.setenv("USER_POOL_ID", setup_environment[0].describe_user_pool(UserPoolId=setup_environment[0].list_user_pools(MaxResults=1)['UserPools'][0]['Id'])['UserPool']['Id'])
    monkeypatch.setenv("USER_POOL_CLIENT_ID", setup_environment[2])

    event = {
        "body": json.dumps({
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
    }
    response = login_app.lambda_handler(event, None)
    assert response["statusCode"] == 200

def test_login_invalid_password(setup_environment, monkeypatch):
    monkeypatch.setenv("USER_POOL_ID", setup_environment[0].describe_user_pool(UserPoolId=setup_environment[0].list_user_pools(MaxResults=1)['UserPools'][0]['Id'])['UserPool']['Id'])
    monkeypatch.setenv("USER_POOL_CLIENT_ID", setup_environment[2])

    event = {
        "body": json.dumps({
            "email": USER_EMAIL,
            "password": INVALID_PASSWORD
        })
    }
    response = login_app.lambda_handler(event, None)
    assert response["statusCode"] == 401

def test_login_unconfirmed_user(setup_environment, monkeypatch):
    monkeypatch.setenv("USER_POOL_ID", setup_environment[0].describe_user_pool(UserPoolId=setup_environment[0].list_user_pools(MaxResults=1)['UserPools'][0]['Id'])['UserPool']['Id'])
    monkeypatch.setenv("USER_POOL_CLIENT_ID", setup_environment[2])

    event = {
        "body": json.dumps({
            "email": UNCONFIRMED_EMAIL,
            "password": USER_PASSWORD
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
