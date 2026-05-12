import json
import os
import boto3
from decimal import Decimal


dynamodb = boto3.resource("dynamodb")
table_name = os.environ["BOOKS_TABLE_NAME"]
books_table = dynamodb.Table(table_name)


def decimal_to_json(obj):
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError


def validate_id(book_id):
    if not book_id:
        return "Book id is required"

    if not str(book_id).isdigit():
        return "Book id must be a number"

    return None


def build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, default=decimal_to_json)
    }


def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        book_id = path_params.get("id")

        id_validation = validate_id(book_id)

        if id_validation:
            return build_response(400, {
                "success": False,
                "error": id_validation
            })

        book_id = int(book_id)

        response = books_table.get_item(
            Key={
                "id": book_id
            }
        )

        book = response.get("Item")

        if not book:
            return build_response(404, {
                "success": False,
                "error": "Book not found"
            })

        books_table.delete_item(
            Key={
                "id": book_id
            }
        )

        return build_response(200, {
            "success": True,
            "message": "Book deleted successfully",
            "data": book
        })

    except Exception as e:
        print("Error deleting book by id:", str(e))

        return build_response(500, {
            "success": False,
            "error": "Internal server error"
        })