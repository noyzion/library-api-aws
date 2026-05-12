import json
import os
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Attr


dynamodb = boto3.resource("dynamodb")

books_table_name = os.environ["BOOKS_TABLE_NAME"]
books_table = dynamodb.Table(books_table_name)

counters_table_name = os.environ["COUNTERS_TABLE_NAME"]
counters_table = dynamodb.Table(counters_table_name)


ALLOWED_GENRES = {
    "fiction",
    "non-fiction",
    "science",
    "history",
    "other",
}


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }


def validate_book(data):
    if "title" not in data or not data["title"]:
        return "title is required"

    if "author" not in data or not data["author"]:
        return "author is required"

    if "isbn" not in data or not data["isbn"]:
        return "isbn is required"

    isbn = str(data["isbn"])

    if len(isbn) != 13:
        return "isbn must be 13 characters long"

    if not isbn.isdigit():
        return "isbn must contain only digits"

    if "genre" not in data or not data["genre"]:
        return "genre is required"

    if data["genre"] not in ALLOWED_GENRES:
        return "genre is not valid"

    if "published_year" not in data:
        return "published_year is required"

    if not isinstance(data["published_year"], int):
        return "published_year must be a number"

    current_year = datetime.now(timezone.utc).year

    if data["published_year"] < 0 or data["published_year"] > current_year:
        return "published_year is not valid"

    if "total_copies" not in data:
        return "total_copies is required"

    if not isinstance(data["total_copies"], int):
        return "total_copies must be a number"

    if data["total_copies"] <= 0:
        return "total_copies must be greater than 0"

    return None


def isbn_exists(isbn):
    result = books_table.scan(
        FilterExpression=Attr("isbn").eq(isbn)
    )

    return len(result.get("Items", [])) > 0


def get_next_book_id():
    result = counters_table.update_item(
        Key={
            "counter_name": "books"
        },
        UpdateExpression="ADD current_value :increment",
        ExpressionAttributeValues={
            ":increment": 1
        },
        ReturnValues="UPDATED_NEW"
    )

    return int(result["Attributes"]["current_value"])


def handler(event, context):
    try:
        if "body" not in event or event["body"] is None:
            return response(400, {
                "success": False,
                "message": "Request body is required"
            })

        try:
            data = json.loads(event["body"])
        except json.JSONDecodeError:
            return response(400, {
                "success": False,
                "message": "Invalid JSON body"
            })

        validation_error = validate_book(data)

        if validation_error:
            return response(400, {
                "success": False,
                "message": validation_error
            })

        isbn = str(data["isbn"])

        if isbn_exists(isbn):
            return response(409, {
                "success": False,
                "message": "Book with this isbn already exists"
            })

        now = datetime.now(timezone.utc).isoformat()
        book_id = get_next_book_id()

        book = {
            "id": book_id,
            "title": data["title"],
            "author": data["author"],
            "isbn": isbn,
            "published_year": data["published_year"],
            "genre": data["genre"],
            "total_copies": data["total_copies"],
            "available_copies": data["total_copies"],
            "created_at": now,
            "updated_at": now
        }

        books_table.put_item(Item=book)

        return response(201, {
            "success": True,
            "data": {
                "id": book_id
            },
            "message": "Book created successfully"
        })

    except Exception as e:
        print("Error creating book:", str(e))

        return response(500, {
            "success": False,
            "message": "Internal server error"
        })