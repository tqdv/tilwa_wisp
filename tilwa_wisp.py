#!/usr/bin/env python3

def put(*args, **kwargs):
    if not hasattr(kwargs, 'end'):
        kwargs['end'] = ""
    print(*args, **kwargs)

# Usage:
#   x = RowCol(row, col)
#   x.row, x.column
class RowCol:
    def __init__(self, row, column):
        self.row = row
        self.column = column

    # eg. {row: 1, column: 5} becomes "1:5"
    def __repr__(self):
        return f"{self.row}:{self.column}"

class UnmatchedParens(Exception):
    pass

class NonTerminatedString(Exception):
    pass

# Given a string, returns a sequence of characters and their position as RowCol
def characters(text):
    column = 0
    row = 0
    position = 0

    while True:
        try:
            # Read the current character
            current_character = text[position]
        except:
            # If that fails, stop everything
            break

        # Process the character
        yield current_character, RowCol(row, column)

        # Compute the position of the next character based on the current character
        if current_character == "\n":
            column = 0
            row += 1
        elif current_character == "\t":
            column += TAB_SIZE
        else:
            column += 1

        # Move the cursor for the next character
        position += 1

LEX_NONE           = 0
LEX_WHITESPACE     = 1
LEX_NEWLINE        = 2
LEX_OPEN_PARENS    = 3
LEX_OPEN_BRACKET   = 4
LEX_OPEN_BRACE     = 5
LEX_NON_WHITESPACE = 6
LEX_CLOSE_PARENS   = 7
LEX_CLOSE_BRACKET  = 8
LEX_CLOSE_BRACE    = 9
LEX_COMMENT        = 12

# Usage:
#   x = Lexeme(LEX_OPEN_PARENS, "(", pos)
#   x.type, x.content, x.position
class Lexeme:
    def __init__(self, type, content, position):
        self.type = type
        self.content = content
        self.position = position
    
    # eg. Lexeme#6<let>@1:2
    def __repr__(self):
        oneline_content = "[NL]" if self.content == "\n" else self.content
        return f"Lexeme#{self.type}<{oneline_content}>@{self.position}"

def lexemes(text):
    chars = characters(text)
    already_read = False # One character look_ahead

    # Each loop iteration yields a new lexeme
    while True:
        # Read the next character if not already done
        if already_read:
            already_read = False
        else:
          try:
            c, pos = next(chars)
          except:
              return
        
        # Start a new lexeme
        lexeme = "" + c
        lexeme_position = pos

        # Handle comments: read until a newline character
        if c == ";":
          try:
            while True:
                c, pos = next(chars)
                if c == "\n":
                    yield Lexeme(LEX_COMMENT, lexeme, lexeme_position)
                    already_read = True
                    break
                else:
                    lexeme += c
          except:
              yield Lexeme(LEX_COMMENT, lexeme, lexeme_position)
              return

        # Handle one character tokens
        elif c == "\n": yield Lexeme(LEX_NEWLINE,       lexeme, lexeme_position)
        elif c == "(":  yield Lexeme(LEX_OPEN_PARENS,   lexeme, lexeme_position)
        elif c == "[":  yield Lexeme(LEX_OPEN_BRACKET,  lexeme, lexeme_position)
        elif c == "{":  yield Lexeme(LEX_OPEN_BRACE,    lexeme, lexeme_position)
        elif c == ")":  yield Lexeme(LEX_CLOSE_PARENS,  lexeme, lexeme_position)
        elif c == "]":  yield Lexeme(LEX_CLOSE_BRACKET, lexeme, lexeme_position)
        elif c == "}":  yield Lexeme(LEX_CLOSE_BRACE,   lexeme, lexeme_position)

        # Handle whitespace: collect as much whitespace characters as possible
        elif c in " \t":
          try:
            while True:
                c, pos = next(chars)
                if c in " \t":
                    lexeme += c
                else:
                    yield Lexeme(LEX_WHITESPACE, lexeme, lexeme_position)
                    already_read = True
                    break
          except:
              yield Lexeme(LEX_WHITESPACE, lexeme, lexeme_position)
              return
        
        # Handle strings
        elif c == '"':
          try:
            while True:
                c, pos = next(chars)
                if c == "\\":
                    lexeme += c
                    c, pos = next(chars)
                    lexeme += c
                if c == '"':
                    lexeme += c
                    yield Lexeme(LEX_STRING, lexeme, lexeme_position)
                    break
          except:
              raise NonTerminatedString()

        
        # Handle non-whitespace: read until any character that would start another lexeme
        else:
          try:
            while True:
                if already_read:
                    already_read = False
                else:
                    c, pos = next(chars)
                
                if c in " \t\n([{}]);":
                    yield Lexeme(LEX_NON_WHITESPACE, lexeme, lexeme_position)
                    already_read = True
                    break
                else:
                    lexeme += c
          except:
              yield Lexeme(LEX_NON_WHITESPACE, lexeme, lexeme_position)
              return

SAX_OPEN  = 0
SAX_NODE  = 1
SAX_CLOSE = 2

class Indentation:
    def __init__(self, indentation_type, column):
        self.type = indentation_type
        self.column = column
    
    def __repr__(self):
        return f"{{{self.type} c{self.column}}}"

PARENS_DOT = 1
PARENS_INDENT = 2
PARENS_PARENS = 3
PARENS_QUOTE = 5
PARENS_MAYBE = 6

COLON_IN_LINE = 1
COLON_AT_END_OF_LINE = 2

# Tag places where we might add parens based on the indentation rule
def sax_parse(text):
    lexed = lexemes(text)

    buffer = []
    indents = []
    lex = None

    def flush_buffer():
        nonlocal buffer
        for e in buffer:
            yield SAX_NODE, e
        buffer.clear()

    def handle_parenthesized_form():
        nonlocal lex

        # Emit the opening parens that triggered this function call
        yield SAX_NODE, lex

        # Consume lexemes until the matching parens
        openers = [lex.type]
        while len(openers) > 0:
            try:
                lex = next(lexed)
            except StopIteration:
                raise UnmatchedParens()

            # Keep track of opening parens
            if lex.type in (LEX_OPEN_PARENS, LEX_OPEN_BRACKET, LEX_OPEN_BRACE):
                openers.append(lex.type)
            # And make sure closing parens close the corresponding opener
            elif lex.type in (LEX_CLOSE_PARENS, LEX_CLOSE_BRACKET, LEX_CLOSE_BRACE):
                last_opener = openers[-1]
                if (lex.type == LEX_CLOSE_PARENS  and last_opener == LEX_OPEN_PARENS
                 or lex.type == LEX_CLOSE_BRACKET and last_opener == LEX_OPEN_BRACKET
                 or lex.type == LEX_CLOSE_BRACE   and last_opener == LEX_OPEN_BRACE):
                    openers.pop()
                else:
                    raise UnmatchedParens()
            
            yield SAX_NODE, lex
    
    # Also buffer the current value of lex
    def buffer_whitespace_and_newlines():
        nonlocal lex
        while True:
            if lex.type in (LEX_WHITESPACE, LEX_COMMENT, LEX_NEWLINE):
                buffer.append(lex)
            else:
                break
            lex = next(lexed)

    def lex_is_colon(lex):
        return lex.type == LEX_NON_WHITESPACE and all([x == ':' for x in lex.content])

    def determine_colon_location():
        nonlocal lex
        while True:
            lex = next(lexed)
            if lex.type == LEX_WHITESPACE or lex.type == LEX_COMMENT:
                buffer.append(lex)
            elif lex.type == LEX_NEWLINE:
                return COLON_AT_END_OF_LINE
            else:
                return COLON_IN_LINE
    
    def handle_colon_in_line(colon):
        for i in range(len(colon.content)):
            indents.append(Indentation(PARENS_INDENT, colon.position.column+i))
            yield SAX_OPEN, None
        buffer.clear() # Discard following whitespace FIXME

    def handle_colon_at_end_of_line(colon, current_indent):
        colon_count = len(colon.content) - 1 # Omit the last one because it's special
        emit_before_ws = max(0, min(colon_count, current_indent - colon.position.column)) # clamp to [0; colon_count]

        col = colon.position.column
        for _ in range(emit_before_ws):
            indents.append(Indentation(PARENS_INDENT, col))
            col += 1
            yield SAX_OPEN, None

        emit_after_ws = colon_count - emit_before_ws
        if emit_after_ws > 0:
            for x in flush_buffer(): yield x
            for _ in range(emit_after_ws):
                indents.append(Indentation(PARENS_INDENT, col))
                col += 1
                yield SAX_OPEN, None
        
        # The last parens may get negated by a dot or a parenthesized form
        indents.append(Indentation(PARENS_MAYBE, col))
    
    def compute_closing(current_indent):
        # Close all parens with an indentation levels greater or equal to the current indent, starting from the deepest indent level
        for i in reversed(range(len(indents))):
            last_parens = indents[i]
            if not (current_indent <= last_parens.column):
                break
            indents.pop()

            # Handle a potential parens from a colon
            if last_parens.type == PARENS_MAYBE:
                yield SAX_OPEN, None
                yield SAX_CLOSE, None
            # PARENS_DOT and PARENS_PARENS don't have an opening parens, so no closing one either
            elif last_parens.type == PARENS_DOT or last_parens.type == PARENS_PARENS:
                pass
            else:
                # We close the block with a parens
                yield SAX_CLOSE, None
    
    def compute_opening():
        nonlocal lex
        indent_type = PARENS_INDENT
        if len(indents) > 0 and indents[-1].type == PARENS_MAYBE:
            indents.pop()

        # At the start of a new block, decide if we open a parens or not
        # Do not open a parens if the block starts with a dot or a parens
        try:
            if lex.type in (LEX_OPEN_PARENS, LEX_CLOSE_BRACKET, LEX_OPEN_BRACE):
                indent_type = PARENS_PARENS
            elif lex.type == LEX_NON_WHITESPACE:
                if lex.content == ".":
                    indent_type = PARENS_DOT
                    # Omit the dot and the following whitespace
                    lex = next(lexed)
                    if lex.type == LEX_WHITESPACE:
                        lex = next(lexed)
                elif lex.content in ("'", ",", "`", ",@", "#'", "#,", "#`", "#,@"):
                    yield SAX_NODE, lex
                    indent_type = PARENS_QUOTE
                    yield SAX_OPEN, None
                    lex = next(lexed) # Omit following whitespace
                    if lex.type == LEX_WHITESPACE:
                        lex = next(lexed)

            if indent_type == PARENS_INDENT:
                yield SAX_OPEN, None
        finally:
            # Keep track of the indentation
            indents.append(Indentation(indent_type, lex.position.column))
        

    try:
        # Each iteration handles a new indented line
        lex = next(lexed)
        while True:
            buffer_whitespace_and_newlines()
            for x in compute_closing(lex.position.column): yield x # Close blocks as needed
            for x in flush_buffer(): yield x                       # Emit optional whitespace
            for x in compute_opening(): yield x                    # Open blocks as needed

            # Processing the line
            while True:
                if lex.type == LEX_WHITESPACE or lex.type == LEX_COMMENT:  # Buffer whitespace and comments
                    buffer.append(lex)
                elif lex.type in (LEX_OPEN_PARENS, LEX_CLOSE_BRACKET, LEX_OPEN_BRACE):
                    for x in flush_buffer(): yield x                       # ^ Skip over parenthesized forms
                    for x in handle_parenthesized_form(): yield x
                elif lex_is_colon(lex):                                    # Handle colons
                    colon_lex = lex
                    for x in flush_buffer(): yield x
                    try:
                        colon_location = determine_colon_location()            #   NB After this call, lex is the next lexeme to process
                        if colon_location == COLON_IN_LINE:                    #   if the colon is inline, emit the corresponding parens
                            for x in handle_colon_in_line(colon_lex): yield x  #     We skip reading a new lexeme before processing them as we already did that
                            continue                                           #     while processing
                        else: # COLON_AT_END_OF_LINE                           #   otherwise, check the next block's indentation to know what to do
                            buffer_whitespace_and_newlines()
                            for x in handle_colon_at_end_of_line(colon_lex, lex.position.column): yield x
                            break                                          #     Handle the new block's indentation (if any)
                    except:
                        for x in handle_colon_at_end_of_line(colon_lex, lex.position.column): yield x
                        raise
                elif lex.type == LEX_NEWLINE:                              # Newlines means new block
                    break
                else:                                                      # By default, passthrough the lexeme
                    for x in flush_buffer(): yield x
                    yield SAX_NODE, lex
                # Read the next lexeme at the end of the loop iteration
                lex = next(lexed)
    except StopIteration:
        for x in compute_closing(0): yield x
        for x in flush_buffer(): yield x

def translate(text):
    saxes = sax_parse(text)

    while True:
        try:
            e = next(saxes)
        except StopIteration:
            break
        
        if e[0] == SAX_OPEN:
            put("(")
        elif e[0] == SAX_CLOSE:
            put(")")

        elif e[0] == SAX_NODE:
            put(e[1].content)


if __name__ == '__main__':
    from sys import stdin
    text = stdin.read()
    translate(text)


# === Archive ===

# Read whitespace characters until you get to the first non-whitespace character, while recording the column number
# Check if the first character of the line is a dot
#  if it is, then don't emit a parens
#  otherwise, do emit a parens
# Anyways, record the indentation level
# And then process the rest of the elements on the line
#   if it's a normal lisp thing, just skip it over
#   if it's a colon, emit a parens, and then try to look for the next printable character 
#      if it's on the same line, record that position
#      otherwise it's on the next line, record the position, and then apply newline rules
#

# Rules
# indent rule: an indentation level adds parentheses
# dot rule: a dot suppresses the parentheses
# colon rule: a colon introduces a new block