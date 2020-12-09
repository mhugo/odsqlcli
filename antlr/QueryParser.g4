parser grammar QueryParser;

options {
	tokenVocab = QueryLexer;
}

ods_field: field=FIELD | field_bq=ods_field_bq;

ods_field_bq:
    FIELD_BQ
    ;

// Full select query. This rule is not currently used (no full access to sql language)
select_query
    : SELECT select_expressions (WHERE condition)? (GROUP BY group_by_expressions)? (ORDER BY order_by_expressions)? (LIMIT limit=numeric_literal)? EOF
    ;

select_parameter
    : select_expressions EOF
    ;

select_expressions
    : select_expression (COMMA select_expression)*
    ;

select_expression
    : select (AS label_id)?
    | select_all
    | include
    | exclude
    ;

include
    : INCLUDE LP include_exclude_expr RP
    ;

exclude
    : EXCLUDE LP include_exclude_expr RP
    ;

include_exclude_expr
    : (FIELD | DOT | MUL)*
    ;

select
    : select_top
    | arithmetic
    ;

select_all
    : MUL
    ;

select_top
    : TOP nb_res=INT? ((ods_field ( COMMA  ods_field)*)| MUL)?
    ;

label_id
    : (FIELD | COUNT | SUM | MIN | MAX | AVG | YEAR | MONTH | DAY | HOUR | MINUTE | SECOND | MILLISECOND | DATE_FORMAT)
    ;

group_by_parameter
    : group_by_expressions EOF
    ;

group_by_expressions:
    group_by_expression (COMMA group_by_expression)*
    ;

group_by_expression
    : group_by (AS label_id)?
    ;

group_by
    : ods_field         # GroupByField
    | group_by_function # GroupByFunction
    ;

group_by_function
    : group_by_range
    | date_function
    | date_format_function
    | group_by_geo_cluster
    ;

group_by_range
    : RANGE LP ods_field COMMA lb=(LSB|RSB) numeric_literal (COMMA  numeric_literal)* hb=(LSB|RSB) RP  # GroupByStaticRange
    | RANGE LP ods_field COMMA EQUI LP int_literal COMMA numeric_literal COMMA numeric_literal RP RP   # GroupByEquiRange
    ;

group_by_geo_cluster
    : GEO_CLUSTER ods_field COMMA cluster_precision=int_literal (COMMA cluster_distance=int_literal)? RP
    ;

order_by_parameter
    : order_by_expressions EOF
    ;

order_by_expressions
    : order_by_expression (COMMA order_by_expression)*
    ;

order_by_expression
    : direction=(PLUS | MINUS)? order_by_operation
    | order_by_operation direction=(ASC | DESC)?
    ;

order_by_operation
    : ods_field       # OrderByField
    | arithmetic      # OrderByExpression
    | sort_function   # OrderByFunction
    ;

sort_function
    : RANDOM LP RP     # RandomSorting
    | RELEVANCE LP RP  # RelevanceSorting
    ;

aggregation_function
    : agg_func=(MAX | MIN | AVG | AVG | SUM) LP arithmetic RP    # AggStat
    | COUNT LP (ods_field | MUL) RP                              # AggCount
    | ENVELOPE LP ods_field? RP                                  # AggEnvelope
    | PERCENTILE LP arithmetic COMMA numeric_literal RP          # AggPercentile
    | MEDIAN LP arithmetic RP                                    # AggMedian
    ;

where_parameter
    : condition EOF
    ;

condition
    : LP condition RP                     # Parenthesis
    | NOT condition                       # Not
    | condition op=AND condition          # Boolean
    | condition op=OR condition           # Boolean
    | expression                          # Single
    |                                     # EmptyExpression
    ;

expression
    : filter_function
    | filter_expression
    | filter_search_query
    ;

filter_function
    : distance_func
    | geometry_func
    | polygon_func
    | bbox_func
    | type_filter
    ;

type_filter
    : IS_TYPE  f_type=(TYPE_INT| TYPE_DOUBLE | TYPE_TEXT | TYPE_FILE | TYPE_DATE | TYPE_DATETIME | TYPE_IMAGE) (COMMA ods_field )? RP
    ;

filter_expression
    : left=arithmetic (op=GT | op=GE | op=LT | op=LE ) right=arithmetic       # ComparisonFilter
    | left=ods_field (op=GT | op=GE | op=LT | op=LE ) right=date              # ComparisonFilter
    | arithmetic (op=EQ |op=NE) arithmetic                                    # EqualityFilter
    | ods_field IS NOT? NULL                                                  # NullFilter
    | ods_field IN range_expression                                           # RangeFilter
    | ods_field IN list_expression                                            # ListFilter
    | ods_field LIKE string_literal                                           # LikeFilter
    | ods_field COLON term_expression                                         # TermFilter
    | ods_field                                                               # BooleanFilter
    | ods_field COLON (value=TRUE|value=FALSE)                                # BooleanFilter
    | ods_field IS (value=TRUE|value=FALSE)                                   # BooleanFilter
    ;

term_expression
    : single_term[True]                                              # SingleTerm
    | LP single_term[True] (AND single_term[True] )* RP              # AndTerm
    | LP single_term[True] (OR  single_term[True] )* RP              # OrTerm
    ;

single_term[bool c]
    : single_term_value                 # SimpleTerm
    | range_expression                  # RangeTerm
    | {$c}? MINUS single_term[False]    # ExcludeTerm
    ;

single_term_value
    : decimal_literal
    | int_literal
    | string_literal
    ;

facet_filter
    : facet_filter AND facet_filter               # AndFacetFilter
    |  ods_field COLON term_expression            # FacetFilter
    ;

range_expression
    : lb=(LSB|RSB) from_val=date_arithmetic RANGE_DELIMITER to_val=date_arithmetic hb=(LSB|RSB)
    ;

list_expression
   : attr_function
   ;

date_arithmetic
    : date | arithmetic
    ;

arithmetic
    : aggregation_function                          # FunctionAggregation
    | geometry_function                             # GeometryFunction
    | unary[True]                                   # SingleArithmetic
    | LP arithmetic RP                              # ArithmeticParenthesis
    | arithmetic (op=MUL | op=DIV ) arithmetic      # Operation
    | arithmetic (op=PLUS | op=MINUS ) arithmetic   # Operation
    ;

unary[bool c]
    : scalar_function                               # ScalarFunction
    | {$c}? (sign=PLUS | sign=MINUS) unary[False]   # UnaryOperator
    | primitiveLiteral                              # UnaryLiteral
    ;

/* scalar functions */

scalar_function
    : length_function
    | now_function
    | attr_function
    | date_function
    | date_format_function
    ;

length_function
    : LENGTH_FUNC  (string_literal | ods_field)  RP
    ;

now_function
    : NOW_FUNC now_function_parameters? RP
    ;

now_function_parameters
    : now_function_parameter (COMMA now_function_parameter)*
    ;

now_function_parameter
    : NOW_WEEKDAY EQ now_value                             # now_weekday_parameter
    | NOW_WEEKDAY EQ NOW_WEEKDAY_DAYS LP now_value? RP     # now_weekday_parameter
    | NOW_KEYWORD EQ now_value                             # now_simple_parameter
    ;

now_value: NOW_ATTR_VALUE;

filter_search_query
    : quoted_text
    ;

quoted_text
    : STRING_SQ | STRING_DQ;

primitiveLiteral
    : ods_field
    | decimal_literal
    | int_literal
    | string_literal
    | geometry
    ;

string_literal : STRING_SQ | STRING_DQ;

numeric_literal : decimal_literal | int_literal;

decimal_literal : DECIMAL;

int_literal : INT;


/* Filter functions */

attr_function : ATTR_FUNC attr_name=string_literal RP;

distance_func : DISTANCE_FUNC ods_field COMMA geometry COMMA distance_val RP;

distance_val: INT | DECIMAL | DISTANCE_VALUE;

geometry_func : GEOMETRY_FUNC ods_field COMMA geometry (COMMA relation=(INTERSECTS | DISJOINT | WITHIN))? RP;

polygon_func : POLYGON_FUNC ods_field COMMA geometry RP;

bbox_func : BBOX_FUNC ods_field COMMA top_left=geometry COMMA bottom_right=geometry RP;

v1_filter_function : V1_FUNC query=string_literal RP;

date
    : DATE_DEF DATE
    ;

date_function
    : date_func_name=(YEAR | MONTH | DAY | HOUR | MINUTE | SECOND | MILLISECOND) LP date_or_field RP
    ;

date_format_function
    : DATE_FORMAT LP ods_field COMMA quoted_text RP
    ;

date_or_field
    : date | ods_field
    ;

/* Geo functions */

geometry_function
    : geo_simplify_function
    | geo_transform_function
    ;

geo_simplify_function
    : SIMPLIFY_FUNC ods_field COMMA int_literal RP
    ;

geo_transform_function
    : TRANSFORM_FUNC ods_field COMMA int_literal RP
    ;

/* Geometries definition */

geometry
    : GEOM GEOMETRY
    ;

select_from
    : SELECT select_expressions FROM table=ods_field (WHERE condition)? (GROUP BY group_by_expressions)? (ORDER BY order_by_expressions)? (LIMIT limit=int_literal)? (OFFSET offset=int_literal)? EOF
    ;
