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
                type=dynamodb.AttributeType.STRING
            ),
            table_name="Books",
            removal_policy=RemovalPolicy.DESTROY.DESTROY
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

