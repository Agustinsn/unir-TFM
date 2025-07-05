# # tests/unit/test_register_unit.py
# import json
# import pytest
# from src.register import app

# @pytest.fixture(scope="module")
# def setup_register_env():
#     # Variables necesarias para pruebas locales (mocked o reales)
#     return {
#         "email": "nuevo@ejemplo.com",
#         "password": "Temp123!"
#     }

# def test_register_success(setup_register_env):
#     event = {
#         "body": json.dumps({
#             "email": setup_register_env["email"],
#             "password": setup_register_env["password"]
#         })
#     }

#     response = app.lambda_handler(event, None)
#     assert response["statusCode"] in [200, 201, 409]  # Si ya existe puede retornar 409
#     assert "message" in json.loads(response["body"])

# def test_register_missing_fields():
#     event = {
#         "body": json.dumps({
#             "email": ""
#         })
#     }
#     response = app.lambda_handler(event, None)
#     assert response["statusCode"] == 400
#     assert "message" in json.loads(response["body"])