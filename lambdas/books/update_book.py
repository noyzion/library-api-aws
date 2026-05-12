import json
import os
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["BOOKS_TABLE_NAME"])

def decimal_to_json(obj):
    if isinstance(obj, Decimal):
        return int(obj)

    raise TypeError

def build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, default=decimal_to_json)
    }

def validate_update_data(data):
    allowed_fields = [
        "title",
        "author",
        "isbn",
        "genre",
        "published_year",
        "total_copies",
        "available_copies"
    ]

    allowed_genres = [
        "fiction",
        "non-fiction",
        "science",
        "history",
        "other"
    ]

    if not data:
        return "Request body cannot be empty"

    for field in data:
        if field not in allowed_fields:
            return f"Field '{field}' is not allowed"

    if "title" in data and data["title"] == "":
        return "Title cannot be empty"

    if "author" in data and data["author"] == "":
        return "Author cannot be empty"

    if "isbn" in data and len(str(data["isbn"])) != 13:
        return "ISBN must be exactly 13 characters"

    if "genre" in data and data["genre"] not in allowed_genres:
        return "Invalid genre"

    if "published_year" in data:
        if not isinstance(data["published_year"], int):
            return "Published year must be a number"

        if data["published_year"] < 0:
            return "Published year cannot be negative"

    if "total_copies" in data:
        if not isinstance(data["total_copies"], int):
            return "Total copies must be a number"

        if data["total_copies"] < 0:
            return "Total copies cannot be negative"

    if "available_copies" in data:
        if not isinstance(data["available_copies"], int):
            return "Available copies must be a number"

        if data["available_copies"] < 0:
            return "Available copies cannot be negative"

    if "total_copies" in data and "available_copies" in data:
        if data["available_copies"] > data["total_copies"]:
            return "Available copies cannot be greater than total copies"

    return None


def handler(event, context):
    try:
        book_id = int(event["pathParameters"]["id"])

        data = json.loads(event["body"])

        validation_error = validate_update_data(data)

        if validation_error:
            return build_response(400, {
                "success": False,
                "error": validation_error
            })

        existing_book = table.get_item(
            Key={
                "id": book_id
            }
        )

        if "Item" not in existing_book:
            return build_response(404, {
                "success": False,
                "error": "Book not found"
            })
        
        current_book = existing_book["Item"]

        if "available_copies" in data and "total_copies" not in data:
            current_total_copies = int(current_book["total_copies"])

            if data["available_copies"] > current_total_copies:
                return build_response(400, {
                    "success": False,
                    "error": "Available copies cannot be greater than current total copies"
                })
            
        if "total_copies" in data and "available_copies" not in data:
            current_available_copies = int(current_book["available_copies"])

            if data["total_copies"] < current_available_copies:
                return build_response(400, {
                    "success": False,
                    "error": "Total copies cannot be smaller than current available copies"
                })
        
        data["updated_at"] = datetime.utcnow().isoformat()

        update_expression = "SET "
        expression_attribute_values = {}

        for key, value in data.items():
            update_expression += f"{key} = :{key}, "
            expression_attribute_values[f":{key}"] = value

        update_expression = update_expression[:-2]

        result = table.update_item(
            Key={
                "id": book_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW"
        )

        return build_response(200, {
            "success": True,
            "data": result["Attributes"],
            "message": "Book updated successfully"
        })

    except Exception as error:
        return build_response(500, {
            "success": False,
            "error": str(error)
        })