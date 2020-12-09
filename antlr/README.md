Lexer/parser update
===================

1/ Copy QueryLexer.g4 and QueryParser.g4 from platform/core/antlr
2/ Launch `make`

The Makefile will add a grammar rule so that a complete `select ... from ...` query can be typed. It adds the required lines to lexer / parser files before calling antlr to generate the final parser.
