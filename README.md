# tilwa_wisp

A [wisp][wisp-homepage] (aka [SRFI-119][srfi-119]) to Lisp translator written in Python 3.6.

I notably don't implement wisp syntax rule 4 concerning leading underscores.

## Usage

The script reads wisp code from stdin, and outputs lisp to stdout.

In practice:

- Open a terminal and launch the script with the command `./tilwa_wisp.py`
- Type or copy-paste your wisp code into the terminal
- Press `Ctrl-D` to end terminal input

And the resulting Lisp code should be printed to the terminal.

## Overview

The `characters` generator function turns a string like `abc 123` into a sequence of characters and their positions:

```
"a", {row: 0, column: 0}
"b", {row: 0, column: 1}
"c", {row: 0, column: 2}
" ", {row: 0, column: 3}
"1", {row: 0, column: 4}
...
```

The `lexemes` generator function takes a string, passes it through the `characters` and processes the sequence of characters and their position, into a sequence of lexemes:

```
LEX_NON_WHITESPACE, "abc", {row: 0, column: 0}
LEX_WHITESPACE,     " ",   {row: 0, column: 3}
LEX_NON_WHITESPACE, "123", {row: 0, column: 4}
```

The `sax_parse` generator function takes a string, passes it through `lexemes` and inserts parenthesis into the sequence:

```
SAX_OPEN, None
SAX_NODE, (LEX_NON_WHITESPACE, "abc", {row: 0, column: 0})
SAX_NODE, (LEX_WHITESPACE, " ", {row:0, column: 3})
SAX_NODE, (LEX_NON_WHITESPACE, "123", {row: 0, column: 4})
SAX_CLOSE, None
```

The `translate` function takes a string, passes it through `sax parse` and writes to the standard output:

```
(abc 123)
```

## Developer notes

The translate function is horrifying and I don't know how to make it simpler.

This implementation is *inspired* by wisp, it doesn't necessarily follow the specification closely.

## See also

- The repository containing reference implementations by Draketo, the author of wisp: https://hg.sr.ht/~arnebab/wisp/

[wisp-homepage]: https://www.draketo.de/software/wisp
[srfi-119]: https://srfi.schemers.org/srfi-119/