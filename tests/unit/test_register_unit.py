# # tests/unit/test_register_unit.py
# import json
# import pytest
# from src.register import app

import json
import pytest
import boto3
from moto import mock_cognitoidp
import sys
import os

# Agrega la ruta al directorio 'src/register' donde está app.js
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/register')))

import app as register_app

@pytest.fixture(scope="module")
def setup_register_env():
    with mock_cognitoidp():
        cognito_client = boto3.client("cognito-idp", region_name="us-east-1")
        
        # Crear User Pool
        pool = cognito_client.create_user_pool(PoolName="test-pool")
        user_pool_id = pool["UserPool"]["Id"]

        # Crear User Pool Client
        client = cognito_client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName="test-client",
            GenerateSecret=False
        )
        client_id = client["UserPoolClient"]["ClientId"]

        yield (cognito_client, user_pool_id, client_id)

def test_register_success(setup_register_env, monkeypatch):
    cognito_client, user_pool_id, client_id = setup_register_env
    
    monkeypatch.setenv("USER_POOL_ID", user_pool_id)
    monkeypatch.setenv("CLIENT_ID", client_id)

    event = {
        "body": json.dumps({
            "email": "nuevo@ejemplo.com",
            "password": "Temp123!"
        })
    }

    response = register_app.register(event, None, cognito_client)
    assert response["statusCode"] in [200, 201]  # 200 para éxito, 201 para creado
    assert "message" in json.loads(response["body"])

def test_register_missing_fields(setup_register_env, monkeypatch):
    cognito_client, user_pool_id, client_id = setup_register_env
    
    monkeypatch.setenv("USER_POOL_ID", user_pool_id)
    monkeypatch.setenv("CLIENT_ID", client_id)

    event = {
        "body": json.dumps({
            "email": ""
        })
    }
    response = register_app.register(event, None, cognito_client)
    assert response["statusCode"] == 400
    assert "message" in json.loads(response["body"])