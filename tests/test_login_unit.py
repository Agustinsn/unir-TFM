import pytest
from unittest.mock import patch, MagicMock
from src.login import app

@patch('boto3.client')
def test_login_success(mock_boto):
    mock_cognito = MagicMock()
    mock_boto.return_value = mock_cognito
    mock_cognito.admin_initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "abc",
            "IdToken": "xyz"
        }
    }

    event = {
        "body": '{"email": "test@example.com", "password": "Abc123$%"}'
    }

    result = app.lambda_handler(event, None)
    assert result["statusCode"] == 200
    assert "AccessToken" in result["body"]