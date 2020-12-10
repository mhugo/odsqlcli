from antlr4 import CommonTokenStream, InputStream
from antlr.MyQueryParserVisitor import MyQueryParserVisitor

from antlr.MyQueryLexer import MyQueryLexer
from antlr.MyQueryParserParser import MyQueryParserParser

class SplitQuery:
    def __init__(self):
        self.select = None  # type: str
        self.from_ = None  # type: str
        self.where = None  # type: str
        self.group_by = None  # type: str
        self.order_by = None  # type: str
        self.limit = None  # type: int
        self.offset = None  # type: int

        self.set_command = None  # type: Tuple[str, int]
        self.show_command = None  # type: str


class SplitVisitor(MyQueryParserVisitor):
    """Just splits an ODSQL query into its components:
    select, where, group_by, order_by, from, limit, offset"""
    def __init__(self):
        self.q = SplitQuery()

    def visitSelect_from(self, ctx):
        self.q.select = ctx.select_expressions().getText()
        self.q.from_ = ctx.table.getText()
        if ctx.condition():
            self.q.where = ctx.condition().getText()
        if ctx.group_by_expressions():
            self.q.group_by = ctx.group_by_expressions().getText()
        if ctx.order_by_expressions():
            self.q.order_by = ctx.order_by_expressions().getText()
        if ctx.limit is not None:
            self.q.limit = int(ctx.limit.getText())
        if ctx.offset is not None:
            self.q.offset = int(ctx.offset.getText())

    def visitSet_command(self, ctx):
        self.q.set_command = (
            ctx.option_name.getText(),
            int(ctx.int_value.getText())
        )

    def visitShow_command(self, ctx):
        if ctx.option_name:
            self.q.show_command = ctx.option_name.getText()
        else:
            self.q.show_command = "all"


def split_query_or_command(sql):
    input_stream = InputStream(sql)

    lexer = MyQueryLexer(input_stream)

    stream = CommonTokenStream(lexer)

    parser = MyQueryParserParser(stream)

    parsed = parser.cli_command()

    visitor = SplitVisitor()
    visitor.visit(parsed)

    return visitor.q
