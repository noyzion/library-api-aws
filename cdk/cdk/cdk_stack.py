from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
)
from constructs import Construct
import os


class CdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        books_table = dynamodb.Table(
            self,
            "BooksTable",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.NUMBER
            ),
            table_name="Books",
            removal_policy=RemovalPolicy.DESTROY
        )
        counters_table = dynamodb.Table(
            self,
            "CountersTable",
            partition_key=dynamodb.Attribute(
                name="counter_name",
                type=dynamodb.AttributeType.STRING
            ),
            table_name="Counters",
            removal_policy=RemovalPolicy.DESTROY
        )
        get_books_lambda = _lambda.Function(
            self,
            "GetBooksFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="get_books.handler",
            code=_lambda.Code.from_asset(
                os.path.join("..", "lambdas", "books")
            ),
            environment={
                "BOOKS_TABLE_NAME": books_table.table_name
            }
        )

        books_table.grant_read_data(get_books_lambda)

        api = apigateway.RestApi(
            self,
            "LibraryApi",
            rest_api_name="Library API"
        )

        books_resource = api.root.add_resource("books")

        books_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(get_books_lambda)
        )

        create_book_lambda = _lambda.Function(
            self,
            "CreateBookFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="create_book.handler",
            code=_lambda.Code.from_asset(
                os.path.join("..", "lambdas", "books")
            ),
            environment={
                "BOOKS_TABLE_NAME": books_table.table_name,
                "COUNTERS_TABLE_NAME": counters_table.table_name
            }
        )

        books_table.grant_read_write_data(create_book_lambda)
        counters_table.grant_read_write_data(create_book_lambda)
        
        books_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(create_book_lambda)
        )

        get_book_by_id_lambda = _lambda.Function(
            self,
            "GetBookByIdFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="get_book_by_id.handler",
            code=_lambda.Code.from_asset(
                os.path.join("..", "lambdas", "books")
            ),
            environment={
                "BOOKS_TABLE_NAME": books_table.table_name
            }
        )

        books_table.grant_read_data(get_book_by_id_lambda)
        
        book_by_id_resource = books_resource.add_resource("{id}")
        book_by_id_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(get_book_by_id_lambda)
        )


