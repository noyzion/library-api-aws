import json
import os
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Attr


dynamodb = boto3.resource("dynamodb")
table_name = os.environ["BOOKS_TABLE_NAME"]
books_table = dynamodb.Table(table_name)

VALID_GENRES = {"fiction", "non-fiction", "science", "history", "other"}

def convert_decimal(obj):
    if isinstance(obj, Decimal):
        return int(obj)

    raise TypeError

def validate_genre(genre):
    if genre is None:
        return None

    if genre not in VALID_GENRES:
        return "Genre must be one of: fiction, non-fiction, science, history, other"

    return None

def build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, default=decimal_to_json)
    }

def decimal_to_json(obj):
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError

def handler(event, context):
    try:
        query_params = event.get("queryStringParameters") or {}
        genre = query_params.get("genre")

        if genre:
            genre = genre.strip().lower()     
        
        genre_validation = validate_genre(genre)

        if genre_validation:
            return build_response(400, {
                "success": False,
                "error": genre_validation
            })
        
        if genre:
            response = books_table.scan(
                FilterExpression=Attr("genre").eq(genre)
            )
        else:
                response = books_table.scan()

        books = response.get("Items", [])

        return build_response(200, {
            "success": True,
            "data": books,
            "message": "Books retrieved successfully"
        })
    
    except Exception as e:
        print("Error getting books:", str(e))

        return build_response(500, {
            "success": False,
            "error": "Internal server error"
        })