from sly import Parser

from Logic import declare_variables, get_variable, get_table, load_variable_to_register, assign_value, \
    concatenate_commands, write_value, add_variables, sub_variables, mul_variables, read_variable, div_variables, \
    mod_variables, copy_of_registers, condition_equal, load_registers
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
        z = concatenate_commands(p.commands, p.command)
        return z

    @_('command')
    def commands(self, p):
        return p.command

    '''
    command
    '''

    @_('')
    def copy_of_registers(self, p):
        print("Registers saved")
        return copy_of_registers()

    @_('')
    def load_registers(self, p):
        print("Registers loaded!")
        return load_registers()

    @_('identifier ASSIGN expression SEMICOLON')
    def command(self, p):
        a = p.identifier
        b = p.expression
        z = assign_value(a, b)
        return z

    @_('IF condition THEN copy_of_registers commands ELSE begin_else_if commands ENDIF')
    def command(self, p):
        print("END if")

    @_('')
    def begin_else_if(self, p):
        print("if else")

    @_('IF condition THEN copy_of_registers commands ENDIF load_registers')
    def command(self, p):
        var1, var2, condition = p.condition
        return condition(var1,var2,concatenate_commands(p.commands,p.load_registers),([],[]))

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
        z = read_variable(p.identifier)
        return z

    @_('WRITE value SEMICOLON')
    def command(self, p):
        z = write_value(p.value)
        return z

    '''
    expression
    '''

    @_('value')
    def expression(self, p):
        z = load_variable_to_register(p.value)
        return z

    @_('blocked_register MOD value')
    def expression(self, p):
        a = p.blocked_register
        z = mod_variables(a, p.value)
        return z

    @_('blocked_register ADD value')
    def expression(self, p):
        a = p.blocked_register
        z = add_variables(a, p.value)
        return z

    @_('blocked_register DIV value')
    def expression(self, p):
        a = p.blocked_register
        z = div_variables(a, p.value)
        return z


    @_('blocked_register SUB value')
    def expression(self, p):
        a = p.blocked_register
        return sub_variables(a, p.value)

    @_('blocked_register MUL value')
    def expression(self, p):
        a = p.blocked_register
        z = mul_variables(a, p.value)
        return z

    @_('value')
    def blocked_register(self, p):
        a = load_variable_to_register(p.value)
        a[0].is_blocked = True
        return a

    @_('value NEQ value',
       'value LWR value',
       'value GTR value',
       'value LEQ value',
       'value GEQ value')
    def condition(self, p):
        print("condition equal etc..")

    # return variable1, viariable2, function
    @_('value EQ value')
    def condition(self, p):
        a = condition_equal
        return p.value0, p.value1, a

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
