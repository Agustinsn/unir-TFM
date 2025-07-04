import json
import boto3
import os
from botocore.exceptions import ClientError

# Clientes de AWS
cognito = boto3.client("cognito-idp")
cloudwatch = boto3.client("cloudwatch")
secrets_client = boto3.client("secretsmanager")

# Nombre del secreto en Secrets Manager
SECRET_NAME = "user-app/secrets"

def get_secret_values(secret_name: str) -> dict:
    """Obtiene y parsea el JSON del secreto dado."""
    resp = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(resp["SecretString"])


def record_failed_login_metric(email: str, reason: str):
    """Envía una métrica personalizada a CloudWatch."""
    try:
        cloudwatch.put_metric_data(
            Namespace="UserLogin",
            MetricData=[{
                "MetricName": "FailedLogin",
                "Dimensions": [
                    {"Name": "Reason", "Value": reason},
                    {"Name": "User",   "Value": email}
                ],
                "Unit": "Count",
                "Value": 1
            }]
        )
    except Exception as e:
        print("Error enviando métrica a CloudWatch:", str(e))


def lambda_handler(event, context):
    # 1) Obtén credenciales de Cognito del entorno o Secrets Manager
    user_pool_id = os.getenv("USER_POOL_ID")
    client_id    = os.getenv("USER_POOL_CLIENT_ID")

    if not user_pool_id or not client_id:
        try:
            secrets = get_secret_values(SECRET_NAME)
            user_pool_id = secrets.get("USER_POOL_ID")
            client_id    = secrets.get("USER_POOL_CLIENT_ID")
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "message": f"No se pudo leer secreto '{SECRET_NAME}': {e}"
                })
            }

    # 2) Parseo y validación del body
    print("Evento recibido:", event)
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid JSON format"})
        }

    email = body.get("email")
    password = body.get("password")
    if not email or not password:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Email and password are required"})
        }

    # 3) Intento de autenticación
    try:
        resp = cognito.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow="ADMIN_USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password
            }
        )
        auth = resp["AuthenticationResult"]
        return {
            "statusCode": 200,
            "body": json.dumps({
                "access_token":  auth.get("AccessToken"),
                "id_token":      auth.get("IdToken"),
                "refresh_token": auth.get("RefreshToken")
            })
        }

    except (cognito.exceptions.UserNotFoundException,
            cognito.exceptions.NotAuthorizedException) as e:
        record_failed_login_metric(email, "InvalidCredentials")
        return {
            "statusCode": 401,
            "body": json.dumps({"message": "Invalid email or password"})
        }

    except cognito.exceptions.UserNotConfirmedException as e:
        record_failed_login_metric(email, "UserNotConfirmed")
        return {
            "statusCode": 403,
            "body": json.dumps({"message": "User not confirmed"})
        }

    except Exception as e:
        record_failed_login_metric(email, "UnknownError")
        print("Error inesperado:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)})
        }
