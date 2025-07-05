import json
import boto3
import os

# Estas serán reemplazables en tests
cognito = boto3.client("cognito-idp")
cloudwatch = boto3.client("cloudwatch")
secrets_client = boto3.client("secretsmanager")

SECRET_NAME = "userapp/env-variables"

def get_secret_values(secret_name: str, secrets_client=secrets_client) -> dict:
    response = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

def lambda_handler(event, context, cognito_client=None, secrets=None):
    cognito_client = cognito_client or cognito
    secrets = secrets or secrets_client

    user_pool_id = os.getenv("USER_POOL_ID")
    client_id = os.getenv("USER_POOL_CLIENT_ID")

    if not user_pool_id or not client_id:
        secrets_data = get_secret_values(SECRET_NAME, secrets)
        user_pool_id = secrets_data.get("USER_POOL_ID")
        client_id = secrets_data.get("USER_POOL_CLIENT_ID")

    try:
        body = json.loads(event["body"])
        email = body.get("email")
        password = body.get("password")

        resp = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow="ADMIN_USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps(resp["AuthenticationResult"])
        }

    except cognito_client.exceptions.NotAuthorizedException:
        return {
            "statusCode": 401,
            "body": json.dumps({"message": "Invalid email or password"})
        }
    except cognito_client.exceptions.UserNotConfirmedException:
        return {
            "statusCode": 403,
            "body": json.dumps({"message": "User not confirmed"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)})
        }
