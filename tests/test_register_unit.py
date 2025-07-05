# tests/test_register_unit.py
import json
import pytest
from unittest.mock import patch, MagicMock

@patch("src.register.app.get_secret_values", return_value={
    "USER_POOL_ID": "fake-pool",
    "USER_POOL_CLIENT_ID": "fake-client"
})
@patch("src.register.app.boto3.client")
def test_register_unit(mock_boto_client, mock_get_secret):
    mock_cognito = MagicMock()
    mock_boto_client.return_value = mock_cognito
    mock_cognito.sign_up.return_value = {}

    from src.register.app import lambda_handler

    event = {"body": json.dumps({"email": "x@x.com", "password": "Abc123$%"})}
    res = lambda_handler(event, None)
    assert res["statusCode"] == 200
    mock_get_secret.assert_called_once_with("userapp/env-variables")
    mock_boto_client.assert_called_with("cognito-idp")
