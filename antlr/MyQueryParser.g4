grammar MyQueryParser;

options {
	tokenVocab = MyQueryLexer;
}

import QueryParser;

select_from
    :
    SELECT select_expressions
    FROM table=ods_field
    (WHERE condition)?
    (GROUP BY group_by_expressions)?
    (ORDER BY order_by_expressions)?
    (LIMIT limit=int_literal)?
    (OFFSET offset=int_literal)?
    EOF
    ;

set_command
    : SET option_name=ods_field EQ int_value=int_literal
    ;

show_command
    : SHOW (option_name=ods_field)?
    ;

cli_command
    : select_from
    | set_command
    | show_command
    ;
