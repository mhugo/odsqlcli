all: MyQueryParser.py

MyQueryParser.g4: QueryParser.g4
	cat $< select_from.g4 | sed s/QueryParser/MyQueryParser/ | sed s/QueryLexer/MyQueryLexer/ > $@

MyQueryLexer.g4: QueryLexer.g4
	sed 's/LIMIT: L I M I T;/LIMIT: L I M I T; OFFSET: O F F S E T;/' $< | sed s/QueryLexer/MyQueryLexer/ > $@

MyQueryParser.py: MyQueryLexer.g4 MyQueryParser.g4
	antlr -visitor -Dlanguage=Python3 -o . $^

clean:
	rm -f MyQueryParser.g4 MyQueryLexer.g4 *.py *.tokens *.interp

.PHONY: all

