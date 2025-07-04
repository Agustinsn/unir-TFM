import unittest
import os
import json
from login import app

class TestLoginIntegration(unittest.TestCase):

    def setUp(self):
        os.environ["USER_POOL_ID"] = "us-east-1_XXXXX"
        os.environ["USER_POOL_CLIENT_ID"] = "YYYYYYYYYYYYYYYYY"

    def test_invalid_credentials(self):
        event = {
            "body": json.dumps({
                "email": "noexiste@fake.com",
                "password": "invalido"
            })
        }
        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 401)

    def test_user_not_confirmed(self):
        # Usa un usuario real sin confirmar
        event = {
            "body": json.dumps({
                "email": "usuario_no_confirmado@example.com",
                "password": "tuPassword"
            })
        }
        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 403)

if __name__ == "__main__":
    unittest.main()
