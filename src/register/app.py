import json
import boto3
import os
from botocore.exceptions import ClientError

# Sólo clientes, no hacemos llamadas aquí
cognito = boto3.client('cognito-idp')
secrets_client = boto3.client('secretsmanager')
SECRET_NAME = "user-app/secrets"

def get_secret_values(secret_name: str) -> dict:
    resp = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(resp['SecretString'])

def lambda_handler(event, context):
    user_pool_id = os.getenv("USER_POOL_ID")
    client_id    = os.getenv("USER_POOL_CLIENT_ID")

    if not user_pool_id or not client_id:
        try:
            _secrets = get_secret_values(SECRET_NAME)
            user_pool_id = _secrets.get("USER_POOL_ID")
            client_id    = _secrets.get("USER_POOL_CLIENT_ID")
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"message": f"No se pudo leer secreto {SECRET_NAME}: {e}"})
            }
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        password = body.get('password')

        if not email or not password:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Email and password are required"})
            }

        cognito.sign_up(
            ClientId=client_id,
            Username=email,
            Password=password,
            UserAttributes=[{"Name": "email", "Value": email}]
        )
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "User registered successfully"})
        }

    except cognito.exceptions.UsernameExistsException:
        return {
            "statusCode": 409,
            "body": json.dumps({"message": "User already exists"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)})
        }
