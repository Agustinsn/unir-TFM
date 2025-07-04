import json
import boto3
import os

client = boto3.client('cognito-idp')

USER_POOL_ID = os.environ.get("USER_POOL_ID")
USER_POOL_CLIENT_ID = os.environ.get("USER_POOL_CLIENT_ID")

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        email = body.get('email')
        password = body.get('password')

        if not email or not password:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Email and password are required"})
            }

        response = client.sign_up(
            ClientId=USER_POOL_CLIENT_ID,
            Username=email,
            Password=password,
            UserAttributes=[
                {"Name": "email", "Value": email}
            ]
        )

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "User registered successfully"})
        }

    except client.exceptions.UsernameExistsException:
        return {
            "statusCode": 409,
            "body": json.dumps({"message": "User already exists"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)})
        }
