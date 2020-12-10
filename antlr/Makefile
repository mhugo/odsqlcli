all: MyQueryParserParser.py

MyQueryParserParser.py: QueryLexer.g4 MyQueryLexer.g4 QueryParser.g4 MyQueryParser.g4
	antlr -visitor -Dlanguage=Python3 -o . MyQueryLexer.g4 MyQueryParser.g4

clean:
	rm -f *.py *.tokens *.interp

.PHONY: all

