import json
import pytest

from src.register.app import lambda_handler

@pytest.mark.integration
def test_register_user_real():
    event = {
        "body": json.dumps({
            "email": "test.integration@example.com",
            "password": "Abc123$%"
        })
    }

    response = lambda_handler(event, None)
    assert response["statusCode"] in [200, 409]
