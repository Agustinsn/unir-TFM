import json
import boto3
import os

# Inicializar clientes de AWS
client = boto3.client("cognito-idp")
cloudwatch = boto3.client("cloudwatch")

USER_POOL_ID = os.environ.get("USER_POOL_ID")
USER_POOL_CLIENT_ID = os.environ.get("USER_POOL_CLIENT_ID")

def record_failed_login_metric(email, reason):
    """Envía una métrica personalizada a CloudWatch."""
    try:
        cloudwatch.put_metric_data(
            Namespace="UserLogin",
            MetricData=[
                {
                    "MetricName": "FailedLogin",
                    "Dimensions": [
                        {"Name": "Reason", "Value": reason},
                        {"Name": "User", "Value": email}
                    ],
                    "Unit": "Count",
                    "Value": 1
                }
            ]
        )
    except Exception as e:
        print("Error enviando métrica a CloudWatch:", str(e))


def lambda_handler(event, context):
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

    try:
        response = client.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=USER_POOL_CLIENT_ID,
            AuthFlow="ADMIN_USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "access_token": response["AuthenticationResult"]["AccessToken"],
                "id_token": response["AuthenticationResult"]["IdToken"],
                "refresh_token": response["AuthenticationResult"]["RefreshToken"]
            })
        }

    except (client.exceptions.UserNotFoundException, client.exceptions.NotAuthorizedException):
        record_failed_login_metric(email, "Invalid credentials")
        return {
            "statusCode": 401,
            "body": json.dumps({"message": "Invalid email or password"})
        }

    except client.exceptions.UserNotConfirmedException:
        record_failed_login_metric(email, "User not confirmed")
        return {
            "statusCode": 403,
            "body": json.dumps({"message": "User not confirmed"})
        }

    except Exception as e:
        record_failed_login_metric(email, "Unknown error")
        print("Error inesperado:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)})
        }
