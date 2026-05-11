import json
import os
import boto3
from decimal import Decimal


dynamodb = boto3.resource("dynamodb")
table_name = os.environ["BOOKS_TABLE_NAME"]
books_table = dynamodb.Table(table_name)


def convert_decimal(obj):
    if isinstance(obj, Decimal):
        return int(obj)

    raise TypeError


def handler(event, context):
    response = books_table.scan()
    books = response.get("Items", [])

    response_body = {
        "success": True,
        "data": books,
        "message": "Books retrieved successfully"
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(response_body, default=convert_decimal)
    }