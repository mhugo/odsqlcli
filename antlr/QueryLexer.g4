lexer grammar QueryLexer;


// Letters for case insensitivity

fragment A     : 'A'|'a';
fragment B     : 'B'|'b';
fragment C     : 'C'|'c';
fragment D     : 'D'|'d';
fragment E     : 'E'|'e';
fragment F     : 'F'|'f';
fragment G     : 'G'|'g';
fragment H     : 'H'|'h';
fragment I     : 'I'|'i';
fragment J     : 'J'|'j';
fragment K     : 'K'|'k';
fragment L     : 'L'|'l';
fragment M     : 'M'|'m';
fragment N     : 'N'|'n';
fragment O     : 'O'|'o';
fragment P     : 'P'|'p';
fragment Q     : 'Q'|'q';
fragment R     : 'R'|'r';
fragment S     : 'S'|'s';
fragment T     : 'T'|'t';
fragment U     : 'U'|'u';
fragment V     : 'V'|'v';
fragment W     : 'W'|'w';
fragment X     : 'X'|'x';
fragment Y     : 'Y'|'y';
fragment Z     : 'Z'|'z';

// Specials characters

SQ             : '\'';
DQ             : '"';
LSB            : '[';
RSB            : ']';
LP             : '(';
RP             : ')';
COMMA          : ',';
PIPE           : '|';
DOT            : '.';
COLON          : ':';
GT             : '>';
GE             : '>=';
LT             : '<';
LE             : '<=';
NE             : '!=';
EQ             : '=';

// Allow spaces before function calls
fragment WS_LP          : [ \t\r\n]* '(';


fragment ALPHA          : [a-zA-Z];
fragment DIGIT          : [0-9];
fragment DIGITS         : DIGIT+;
fragment ODS_CHARACTER  : ALPHA | DIGIT | '_' | '.';

PLUS: '+';
MINUS: '-';

MUL         : '*';
DIV         : '/';

IN          : I N;
IS          : I S;
LIKE        : L I K E;
IS_TYPE     : T Y P E WS_LP -> pushMode(MODE_ODS_TYPE);

// Primary types

INT            : DIGITS;
DECIMAL        : INT '.' DIGITS (('e'|'E') DIGITS)?;


// Expression tokens

AND         : A N D ;
OR          : O R;
NOT         : N O T;

GEOM: G E O M SQ -> pushMode(MODE_ODS_GEOM);
DATE_DEF: D A T E SQ -> pushMode(MODE_ODS_DATE);

DISTANCE_FUNC: D I S T A N C E WS_LP -> pushMode(MODE_ODS_DISTANCE);
SIMPLIFY_FUNC: S I M P L I F Y WS_LP;
TRANSFORM_FUNC: T R A N S F O R M WS_LP;
GEO_CLUSTER: G E O '_' C L U S T E R WS_LP;


RANGE_DELIMITER: ('..' | 'TO');

// ODS SQL words

SELECT: S E L E C T;

FROM: F R O M;

TOP: T O P;

LIMIT: L I M I T;

WHERE: W H E R E;

TRUE: T R U E;

FALSE: F A L S E;

AS: A S;

ASC: A S C;

DESC: D E S C;

SUM: S U M;

MAX: M A X;

MIN: M I N;

COUNT: C O U N T;

AVG: A V G;

GROUP: G R O U P;

ORDER: O R D E R;

BY: B Y;

RANGE: R A N G E;

EQUI: E Q U I;

STATIC: S T A T I C;

NULL: N U L L;

ENVELOPE: E N V E L O P E;

INCLUDE : I N C L U D E;

EXCLUDE: E X C L U D E;

PERCENTILE: P E R C E N T I L E;

MEDIAN: M E D I A N;

GEOMETRY_FUNC: G E O M E T R Y WS_LP;

POLYGON_FUNC: P O L Y G O N WS_LP;

BBOX_FUNC: B B O X WS_LP;

LENGTH_FUNC: L E N (G T H)? WS_LP;

ATTR_FUNC: A T T R WS_LP;

NULL_FUNC: N U L L WS_LP;

NOW_FUNC: N O W WS_LP -> pushMode(MODE_ODS_NOW);

V1_FUNC: V '1' WS_LP;

INTERSECTS: I N T E R S E C T S;
DISJOINT: D I S J O I N T;
WITHIN: W I T H I N;


// Sort functions

RANDOM: R A N D O M;
RELEVANCE: R E L E V A N C E;

// Date functions

YEAR        : Y E A R;
MONTH       : M O N T H;
DAY         : D A Y;
HOUR        : H O U R;
MINUTE      : M I N U T E;
SECOND      : S E C O N D;
MILLISECOND : M I L L I S E C O N D;
DATE_FORMAT : D A T E '_' F O R M A T;

// "normal" field names are unquoted, but must start with a letter

FIELD : (ALPHA | '_') ODS_CHARACTER*;

// "special" field names that may start with any characters must be quoted by backquotes

FIELD_BQ
    : '`' ~('`')+ '`';

STRING_SQ
    : '\'' (~('\'' | '\\' | '\r' | '\n') | '\\' ('\'' | '\\'))* '\''
//   : '\'' .*? '\''
//   | '\\\'' .*? '\\\''
   ;


STRING_DQ
   : '"' (~('"' | '\\' | '\r' | '\n') | '\\' ('"' | '\\'))* '"'
//   : '"' .*? '"'
   ;

WS  : [ \t\r\n]+ -> skip;

ErrorCharacter : . ;

mode MODE_ODS_DISTANCE;


DISTANCE_EQ: EQ -> type(EQ);
DISTANCE_COMMA: ',' -> type(COMMA);
DISTANCE_INT     : INT -> type(INT);
DISTANCE_DECIMAL : DECIMAL  -> type(DECIMAL);
DISTANCE_LP: '(' -> type(LP);
DISTANCE_RP: ')' -> type(RP), popMode;

fragment DISTANCE_UNIT: ('mi' | 'yd' | 'ft' | 'm' | 'cm' | 'km' | 'mm');
DISTANCE_VALUE: (DISTANCE_INT | DISTANCE_DECIMAL) [ \t\r\n]* DISTANCE_UNIT;

DISTANCE_GEOMETRY: G E O M SQ -> type(GEOM), pushMode(MODE_ODS_GEOM);
DISTANCE_FIELD : FIELD -> type(FIELD);
DISTANCE_FIELD_BQ : FIELD_BQ -> type(FIELD_BQ);
DISTANCE_WS  : [ \t\r\n]+ -> skip;

mode MODE_ODS_NOW;

NOW_KEYWORD: ('year'
              | 'years'
              | 'month'
              | 'months'
              | 'day'
              | 'days'
              | 'week'
              | 'weeks'
              | 'minute'
              | 'minutes'
              | 'second'
              | 'seconds'
              | 'microsecond'
              | 'microseconds')
              ;

NOW_WEEKDAY: 'weekday';
NOW_WEEKDAY_DAYS: 'MO' | 'TU' | 'WE' | 'TH' | 'FR' | 'SA' | 'SU';

NOW_ATTR_VALUE: ('-'| '+')? DIGITS;

NOW_EQ: EQ -> type(EQ);
NOW_COMMA: ',' -> type(COMMA);
NOW_LP: '(' -> type(LP);
NOW_RP: ')' -> type(RP), popMode;
NOW_WS: [ \t\r\n]+ -> skip;

mode MODE_ODS_TYPE;

TYPE_INT       : I N T;
TYPE_DOUBLE    : D O U B L E;
TYPE_TEXT      : T E X T;
TYPE_FILE      : F I L E;
TYPE_DATE      : D A T E;
TYPE_DATETIME  : D A T E T I M E;
TYPE_IMAGE     : I M A G E;


TYPE_FIELD     : FIELD -> type(FIELD);
TYPE_FIELD_BQ  : FIELD_BQ -> type(FIELD_BQ);
TYPE_COMMA     : COMMA -> type(COMMA);
TYPE_LP        : LP -> type(LP);
TYPE_RP        : RP -> type(RP), popMode;
TYPE_WS        : [ \t\r\n]+ -> skip;


mode MODE_ODS_GEOM;

GEOMETRY : '\'' -> popMode;
GEOM_VAL : . -> more;


mode MODE_ODS_DATE;

DATE     : '\'' -> popMode;
DATE_VAL : . -> more;

mode MODE_ODS_LABEL;

LABEL_COMMA: COMMA -> type(COMMA), popMode;
LABEL_EOF: EOF -> type(EOF), popMode;

LABEL     : ~[, ]+;
LABEL_WS  : [ \t\r\n]+ -> skip;
