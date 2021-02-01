# A Command Line Interface for ODSQL

This is an interactive command line interface that can be used to request ODS Explore API v2 endpoints.

It supports autocompletion, syntax highlighting, multiline input, and history.

## Screenshot

[![asciicast](https://asciinema.org/a/YvJ72VhTgopwI7n4zlx8cN1oJ.svg)](https://asciinema.org/a/YvJ72VhTgopwI7n4zlx8cN1oJ)

## Installation

It is currently designed in order to easily test API v2 features on different code branches.
The ODSQL parser is reused (and augmented a bit).

Rather then messing with git submodules, the link to the platform's parser can be made with simple symbolic links.
Nothing is automated yet.

Possible installation (in a Python 3 virtual env):
```
ln -s <PATH_TO_PLATFORM>/antlr/Query{Parser,Lexer}.g4 antlr
./odsql -h http://testdomain.localhost:8000 -u odsadmin -p coincoin
```

This will call make and then antlr to compile the parser if needed.

## Extra commands

You can input simple SQL queries and ODSQLCLI will choose which endpoint to communicate with.

Some extra commands exist:

- `SHOW [option]` : show current values of options
- `SET option=intvalue` : to set an option

The option `debug` can be set to 1 to output debugging information.

## SQL tables

The SQL `from` clause has been added to specify on which dataset the query must be sent.

The special table `catalog` can be used to list the existing datasets on a domain.



