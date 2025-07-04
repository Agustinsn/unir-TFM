import pytest
from unittest.mock import patch, MagicMock
from src.register import app

@patch('boto3.client')
def test_register_success(mock_boto):
    mock_cognito = MagicMock()
    mock_boto.return_value = mock_cognito
    mock_cognito.admin_create_user.return_value = {}
    mock_cognito.admin_set_user_password.return_value = {}

    event = {
        "body": '{"email": "test@example.com", "password": "Abc123$%"}'
    }

    result = app.lambda_handler(event, None)
    assert result["statusCode"] == 200
    assert "message" in result["body"]
