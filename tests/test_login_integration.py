import os
import json
from src.login import app

def test_login_user_real():
    event = {
        "body": json.dumps({
            "email": "test.integration@example.com",
            "password": "Abc123$%"
        })
    }

    response = app.lambda_handler(event, None)
    assert response["statusCode"] in [200, 401]
