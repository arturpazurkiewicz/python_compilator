from sly import Parser

from MyLexer import MyLexer
from Logic import *

class MyParser(Parser):
    tokens = MyLexer.tokens
    precedence = (
        ('left', ADD, SUB),
        ('left', MUL, DIV),
    )
    '''
    program
    '''

    @_('DECLARE declarations BEGIN commands END')
    def program(self, p):
        print("END")

    @_('BEGIN commands END')
    def program(self, p):
        print("END")

    '''
    declarations
    '''

    @_('declarations COMMA PIDENTIFIER')
    def declarations(self, p):
        declare_variables(p.PIDENTIFIER)

    @_('declarations COMMA PIDENTIFIER LBR NUMBER COLON NUMBER RBR')
    def declarations(self, p):
        declare_variables(p.PIDENTIFIER, p.NUMBER0, p.NUMBER1)

    @_('PIDENTIFIER')
    def declarations(self, p):
        declare_variables(p.PIDENTIFIER)

    @_('PIDENTIFIER LBR NUMBER COLON NUMBER RBR')
    def declarations(self, p):
        declare_variables(p.PIDENTIFIER, p.NUMBER0, p.NUMBER1)

    '''
    commands
    '''

    @_('commands command')
    def commands(self, p):
        print("Commands")

    @_('command')
    def commands(self, p):
        print("Commands")

    '''
    command
    '''

    @_('identifier ASSIGN expression SEMICOLON')
    def command(self, p):
        print("ASSIGN")

    @_('IF condition THEN commands ELSE begin_else_if commands ENDIF')
    def command(self, p):
        print("END if")

    @_('')
    def begin_else_if(self, p):
        print("if else")

    @_('IF condition THEN commands ENDIF')
    def command(self, p):
        print("END if")

    @_('WHILE begin_while condition DO commands ENDWHILE')
    def command(self, p):
        print("end while")

    @_('REPEAT begin_while commands UNTIL condition SEMICOLON')
    def command(self, p):
        print("end repeat")

    @_('')
    def begin_while(self, p):
        print("while")

    @_('FOR PIDENTIFIER FROM value TO value DO begin_for_to commands ENDFOR')
    def command(self, p):
        print("end for to")

    @_('')
    def begin_for_to(self, p):
        print("begin for to")

    @_('FOR PIDENTIFIER FROM value DOWNTO value DO begin_for_downto commands ENDFOR')
    def command(self, p):
        print("end for downto")

    @_('')
    def begin_for_downto(self, p):
        print("begin for downto")

    @_('READ identifier SEMICOLON')
    def command(self, p):
        print("read")

    @_('WRITE value SEMICOLON')
    def command(self, p):
        print("write")

    '''
    expression
    '''

    @_('value')
    def expression(self, p):
        print("expression value")

    @_('value ADD value',
       'value SUB value',
       'value MUL value',
       'value DIV value',
       'value MOD value')
    def expression(self, p):
        print("expression add etc..")

    @_('value EQ value',
       'value NEQ value',
       'value LWR value',
       'value GTR value',
       'value LEQ value',
       'value GEQ value')
    def condition(self, p):
        print("condition equal etc..")

    '''
       value
    '''

    @_('NUMBER')
    def value(self, p):
        print("NUMBER")

    @_('identifier')
    def value(self, p):
        print("identifier")

    '''
       identifier
    '''

    @_('PIDENTIFIER')
    def identifier(self, p):
        print("Pidentifier")

    @_('PIDENTIFIER LBR PIDENTIFIER RBR')
    def identifier(self, p):
        print("table by identifier")

    @_('PIDENTIFIER LBR NUMBER RBR')
    def identifier(self, p):
        print("table by number")

    def error(self, token):
        raise Exception("Syntax error in grammar")
