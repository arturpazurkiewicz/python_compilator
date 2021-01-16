from sly import Lexer


class MyLexer(Lexer):
    tokens = {DECLARE, BEGIN, END, ASSIGN, IF, THEN, ELSE, ENDIF, WHILE, DO, ENDWHILE, REPEAT, UNTIL, FOR, FROM, TO,
              ENDFOR, DOWNTO, READ, WRITE, ADD, SUB, MUL, DIV, MOD, EQ, NEQ,
              RGTR, LGTR, REQ, LEQ,
              SEMICOLON, COLON, COMMA, LBR, RBR, PIDENTIFIER, NUMBER}

    DECLARE = r'DECLARE'
    BEGIN = r'BEGIN'
    ENDFOR = r'ENDFOR'
    DOWNTO = r'DOWNTO'
    ENDIF = r'ENDIF'
    ENDWHILE = r'ENDWHILE'

    END = r'END'
    ASSIGN = r':='
    IF = r'IF'
    THEN = r'THEN'
    ELSE = r'ELSE'
    WHILE = r'WHILE'
    DO = r'DO'
    REPEAT = r'REPEAT'
    UNTIL = r'UNTIL'
    FOR = r'FOR'
    FROM = r'FROM'
    TO = r'TO'

    READ = r'READ'
    WRITE = r'WRITE'
    ADD = r'\+'
    SUB = r'\-'
    MUL = r'\*'
    DIV = r'\/'
    MOD = r'\%'
    REQ = r'<='
    LEQ = r'>='
    EQ = r'='
    NEQ = r'!='
    RGTR = r'<'
    LGTR = r'>'
    SEMICOLON = r';'
    COLON = r':'
    COMMA = r','
    LBR = r'\('
    RBR = r'\)'
    PIDENTIFIER = r'[_a-z]+'

    @_(r'\d+')
    def NUMBER(self, t):
        t.value = int(t.value)
        return t

    ignore = " \t\r"
    ignore_comment = r'\[[^\]]*\]'

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    def error(self, t):
        raise Exception("Syntax error")
