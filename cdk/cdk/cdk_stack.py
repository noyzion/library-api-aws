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

        books_table = self.create_books_table()
        counters_table = self.create_counters_table()

        api = apigateway.RestApi(
            self,
            "LibraryApi",
            rest_api_name="Library API"
        )

        books_resource = api.root.add_resource("books")
        book_by_id_resource = books_resource.add_resource("{id}")

        self.add_books_routes(
            books_table=books_table,
            counters_table=counters_table,
            books_resource=books_resource,
            book_by_id_resource=book_by_id_resource
        )

    def create_books_table(self):
        return dynamodb.Table(
            self,
            "BooksTable",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.NUMBER
            ),
            table_name="Books",
            removal_policy=RemovalPolicy.DESTROY
        )

    def create_counters_table(self):
        return dynamodb.Table(
            self,
            "CountersTable",
            partition_key=dynamodb.Attribute(
                name="counter_name",
                type=dynamodb.AttributeType.STRING
            ),
            table_name="Counters",
            removal_policy=RemovalPolicy.DESTROY
        )

    def create_books_lambda(self, id, handler, books_table, extra_environment=None):
        environment = {
            "BOOKS_TABLE_NAME": books_table.table_name
        }

        if extra_environment:
            environment.update(extra_environment)

        return _lambda.Function(
            self,
            id,
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler=handler,
            code=_lambda.Code.from_asset(
                os.path.join("..", "lambdas", "books")
            ),
            environment=environment
        )

    def add_books_routes(
        self,
        books_table,
        counters_table,
        books_resource,
        book_by_id_resource
    ):
        get_books_lambda = self.create_books_lambda(
            id="GetBooksFunction",
            handler="get_books.handler",
            books_table=books_table
        )

        books_table.grant_read_data(get_books_lambda)

        books_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(get_books_lambda)
        )

        create_book_lambda = self.create_books_lambda(
            id="CreateBookFunction",
            handler="create_book.handler",
            books_table=books_table,
            extra_environment={
                "COUNTERS_TABLE_NAME": counters_table.table_name
            }
        )

        books_table.grant_read_write_data(create_book_lambda)
        counters_table.grant_read_write_data(create_book_lambda)

        books_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(create_book_lambda)
        )

        get_book_by_id_lambda = self.create_books_lambda(
            id="GetBookByIdFunction",
            handler="get_book_by_id.handler",
            books_table=books_table
        )

        books_table.grant_read_data(get_book_by_id_lambda)

        book_by_id_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(get_book_by_id_lambda)
        )

        update_book_lambda = self.create_books_lambda(
            id="UpdateBookFunction",
            handler="update_book.handler",
            books_table=books_table
        )

        books_table.grant_read_write_data(update_book_lambda)

        book_by_id_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(update_book_lambda)
        )