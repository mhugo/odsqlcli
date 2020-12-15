from antlr4 import CommonTokenStream, InputStream, TerminalNode
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
        self.has_aggregate = False


class SplitVisitor(MyQueryParserVisitor):
    """Just splits an ODSQL query into its components:
    select, where, group_by, order_by, from, limit, offset"""
    def __init__(self, input_text):
        self._input_text = input_text
        self.q = SplitQuery()

    def visitSelect_from(self, ctx):
        def _raw_text(ctx):
            return self._input_text[
                ctx.start.start:ctx.stop.stop + 1]

        self.q.select = _raw_text(ctx.select_expressions())
        self.q.from_ = _raw_text(ctx.table)
        if ctx.condition():
            self.q.where = _raw_text(ctx.condition())
        if ctx.group_by_expressions():
            self.q.group_by = _raw_text(ctx.group_by_expressions())
        if ctx.order_by_expressions():
            self.q.order_by = _raw_text(ctx.order_by_expressions())
        if ctx.limit is not None:
            self.q.limit = int(ctx.limit.getText())
        if ctx.offset is not None:
            self.q.offset = int(ctx.offset.getText())
        return self.visitChildren(ctx)

    def visitSet_command(self, ctx):
        self.q.set_command = (
            ctx.option_name.getText(),
            int(ctx.int_value.getText())
        )

    def visitFunctionAggregation(self, ctx):
        self.q.has_aggregate = True

    def visitShow_command(self, ctx):
        if ctx.option_name:
            self.q.show_command = ctx.option_name.getText()
        else:
            self.q.show_command = "all"


def print_rule_tree(tree, rule_names, indent=0):
    if isinstance(tree, TerminalNode):
        print(" " * indent, tree.getSymbol())
    else:
        idx = tree.getRuleIndex()
        print(" " * indent, tree.__class__, rule_names[idx])
        for child in tree.getChildren():
            print_rule_tree(child, rule_names, indent + 2)


def split_query_or_command(sql, debug=False):
    # type: (str) -> SplitQuery

    input_stream = InputStream(sql)

    lexer = MyQueryLexer(input_stream)

    stream = CommonTokenStream(lexer)

    parser = MyQueryParserParser(stream)

    parsed = parser.cli_command()

    #print(parsed, parsed.toStringTree(parser.ruleNames))
    if debug:
        print_rule_tree(parsed, parser.ruleNames)

    visitor = SplitVisitor(sql)
    visitor.visit(parsed)

    return visitor.q
