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

def validate_id(book_id):
    if not book_id:
        return "Book id is required"

    if not book_id.isdigit():
        return "Book id must be a number"

    return None

def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, default=convert_decimal)
    }

def handler(event, context):
    try:
        path_parameters = event.get("pathParameters")
        if not path_parameters or "id" not in path_parameters:
            return response(400, {
                "success": False,
                "message": "Book id is required"
            })
        book_id = event["pathParameters"]["id"]
        validation_error = validate_id(book_id)
    
        if(validation_error):
            return response(400, {
                "success": False,
                "message": validation_error
            })
        
        result = books_table.get_item(
            Key={
                "id": int(book_id)
            }
        )

        book = result.get("Item")

        if not book:
            return response(404, {
                "success": False,
                "message": "Book not found"
            })

        return response(200, {
            "success": True,
            "data": book,
            "message": "Book retrieved successfully"
        })
    
    except Exception as e:
        print("Error getting book by id:", str(e))

        return response(500, {
            "success": False,
            "message": "Internal server error"
        })