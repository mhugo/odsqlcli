select_from
    :
    SELECT? select_expressions
    FROM table=ods_field
    (WHERE condition)?
    (GROUP BY group_by_expressions)?
    (ORDER BY order_by_expressions)?
    (LIMIT limit=int_literal)?
    (OFFSET offset=int_literal)?
    EOF
    ;
