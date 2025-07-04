import unittest
from login import app

class TestLoginFunction(unittest.TestCase):

    def test_missing_email(self):
        event = {"body": '{"password": "123"}'}
        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)

    def test_missing_password(self):
        event = {"body": '{"email": "test@example.com"}'}
        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)

    def test_invalid_json(self):
        event = {"body": 'not-a-json'}
        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)

if __name__ == "__main__":
    unittest.main()
