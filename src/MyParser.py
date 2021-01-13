from sly import Parser

from Logic import declare_variables, get_variable, get_table, load_variable_to_register, assign_value, \
    concatenate_commands
from MyLexer import MyLexer


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
        return p.commands[0]

    @_('BEGIN commands END')
    def program(self, p):
        return p.commands[0]

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
        return concatenate_commands(p.commands, p.command)

    @_('command')
    def commands(self, p):
        return p.command

    '''
    command
    '''

    @_('identifier ASSIGN expression SEMICOLON')
    def command(self, p):
        a = p.identifier
        b = p.expression
        return assign_value(a, b)

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
        return write_value(p.value)


    '''
    expression
    '''

    @_('value')
    def expression(self, p):
        return load_variable_to_register(p.value)

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
        return get_variable(p.NUMBER)

    @_('identifier')
    def value(self, p):
        return p.identifier

    '''
       identifier
    '''

    @_('PIDENTIFIER')
    def identifier(self, p):
        return get_variable(p.PIDENTIFIER)

    @_('PIDENTIFIER LBR PIDENTIFIER RBR')
    def identifier(self, p):
        a = get_table(p.PIDENTIFIER0, get_variable(p.PIDENTIFIER1))
        return a

    @_('PIDENTIFIER LBR NUMBER RBR')
    def identifier(self, p):
        a = get_table(p.PIDENTIFIER, get_variable(p.NUMBER))
        return a

    def error(self, token):
        raise Exception("Syntax error in grammar")
