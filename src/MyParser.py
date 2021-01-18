from sly import Parser

from Logic import declare_variables, get_variable, get_table, load_variable_to_register, assign_value, \
    concatenate_commands, write_value, add_variables, sub_variables, mul_variables, read_variable, div_variables, \
    mod_variables, copy_of_registers, condition_eq, load_registers, prepare_condition_result, condition_neq, \
    condition_lgtr, condition_rgtr, condition_req, condition_leq, remove_copy_of_registers, begin_for, \
    create_for_to, create_for_downto, ConditionMode, check_is_assigned
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
        return p.commands

    @_('BEGIN commands END')
    def program(self, p):
        return p.commands

    '''
    declarations
    '''

    @_('declarations COMMA PIDENTIFIER')
    def declarations(self, p):
        declare_variables(p.PIDENTIFIER,line=p.lineno)

    @_('declarations COMMA PIDENTIFIER LBR NUMBER COLON NUMBER RBR')
    def declarations(self, p):
        declare_variables(p.PIDENTIFIER, p.NUMBER0, p.NUMBER1,p.lineno)

    @_('PIDENTIFIER')
    def declarations(self, p):
        declare_variables(p.PIDENTIFIER, line=p.lineno)

    @_('PIDENTIFIER LBR NUMBER COLON NUMBER RBR')
    def declarations(self, p):
        declare_variables(p.PIDENTIFIER, p.NUMBER0, p.NUMBER1,p.lineno)

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
        # print("Registers saved")
        return copy_of_registers()

    @_('')
    def load_registers(self, p):
        # print("Registers loaded!")
        return load_registers()

    @_('identifier ASSIGN expression SEMICOLON')
    def command(self, p):
        a = p.identifier
        b = p.expression
        z = assign_value(a, b, p.lineno)
        return z

    @_('IF condition THEN copy_of_registers commands ELSE load_registers commands ENDIF load_registers')
    def command(self, p):
        reg1, reg2, var1, var2, cond_str, condition = p.condition
        string = condition(reg1, reg2, var1, var2,
                           concatenate_commands(p.commands0, p.load_registers0),
                           concatenate_commands(p.commands1, p.load_registers1), mode=ConditionMode.is_if)
        remove_copy_of_registers()
        return cond_str + string

    @_('IF condition THEN copy_of_registers commands ENDIF load_registers')
    def command(self, p):
        reg1, reg2, var1, var2, cond_str, condition = p.condition
        string = condition(reg1, reg2, var1, var2, concatenate_commands(p.commands, p.load_registers), [],
                           mode=ConditionMode.is_if)
        remove_copy_of_registers()
        return cond_str + string

    @_('WHILE condition DO copy_of_registers commands ENDWHILE load_registers')
    def command(self, p):
        reg1, reg2, var1, var2, cond_str, condition = p.condition
        string = condition(reg1, reg2, var1, var2, concatenate_commands(p.commands, p.load_registers), [],
                           mode=ConditionMode.is_while, cond_str=cond_str)
        remove_copy_of_registers()
        return cond_str + string

    # load_registers inside method!!!
    @_('REPEAT copy_of_registers commands UNTIL condition SEMICOLON')
    def command(self, p):
        reg1, reg2, var1, var2, cond_str, condition = p.condition
        string = condition(reg1, reg2, var1, var2, p.commands, [],
                           mode=ConditionMode.is_repeat, cond_str=cond_str)
        remove_copy_of_registers()
        return string

    # load_registers inside method!!!
    @_(
        'FOR PIDENTIFIER  FROM value TO value DO copy_of_registers begin_for copy_of_registers commands ENDFOR load_registers')
    def command(self, p):
        return create_for_to(p.begin_for, concatenate_commands(p.commands, p.load_registers))

    @_('')
    def begin_for(self, p):
        return begin_for(p[-7], p[-5], p[-3],self.lines)

    @_(
        'FOR PIDENTIFIER  FROM value DOWNTO value DO copy_of_registers begin_for copy_of_registers commands ENDFOR load_registers')
    def command(self, p):
        return create_for_downto(p.begin_for, concatenate_commands(p.commands, p.load_registers))

    @_('READ identifier SEMICOLON')
    def command(self, p):
        z = read_variable(p.identifier,p.lineno)
        return z

    @_('WRITE value SEMICOLON')
    def command(self, p):
        z = write_value(p.value, p.lineno)
        return z

    '''
    expression
    '''

    @_('value')
    def expression(self, p):
        check_is_assigned(p.value,self.lines)
        z = load_variable_to_register(p.value)
        return z

    @_('blocked_register MOD value')
    def expression(self, p):
        a = p.blocked_register
        z = mod_variables(a, p.value, p[-5],p.lineno)
        return z

    @_('blocked_register ADD value')
    def expression(self, p):
        y = p[-5]
        a = p.blocked_register
        z = add_variables(a, p.value, y,p.lineno)
        return z

    @_('blocked_register DIV value')
    def expression(self, p):
        a = p.blocked_register
        z = div_variables(a, p.value, p[-5],p.lineno)
        return z

    @_('blocked_register SUB value')
    def expression(self, p):
        a = p.blocked_register
        return sub_variables(a, p.value, p[-5], p.lineno)

    @_('blocked_register MUL value')
    def expression(self, p):
        a = p.blocked_register
        z = mul_variables(a, p.value, p[-5], p.lineno)
        return z

    @_('value')
    def blocked_register(self, p):
        check_is_assigned(p.value, self.lines)
        a = load_variable_to_register(p.value)
        a[0].is_blocked = True
        return a

    @_('value RGTR value', )
    def condition(self, p):
        return prepare_condition_result(p.value0, p.value1, condition_rgtr)

    @_('value LGTR value', )
    def condition(self, p):
        return prepare_condition_result(p.value0, p.value1, condition_lgtr)

    @_('value REQ value', )
    def condition(self, p):
        return prepare_condition_result(p.value0, p.value1, condition_req)

    @_('value LEQ value', )
    def condition(self, p):
        return prepare_condition_result(p.value0, p.value1, condition_leq)

    # return variable1, viariable2, function
    @_('value EQ value')
    def condition(self, p):
        return prepare_condition_result(p.value0, p.value1, condition_eq)

    @_('value NEQ value')
    def condition(self, p):
        return prepare_condition_result(p.value0, p.value1, condition_neq)

    '''
       value
    '''

    @_('NUMBER')
    def value(self, p):
        return get_variable(p.NUMBER, p.lineno)

    @_('identifier')
    def value(self, p):
        return p.identifier

    '''
       identifier
    '''

    @_('PIDENTIFIER')
    def identifier(self, p):
        self.lines = p.lineno
        return get_variable(p.PIDENTIFIER,p.lineno)

    @_('PIDENTIFIER LBR PIDENTIFIER RBR')
    def identifier(self, p):
        self.lines = p.lineno
        a = get_table(p.PIDENTIFIER0, get_variable(p.PIDENTIFIER1,p.lineno), p.lineno)
        return a

    @_('PIDENTIFIER LBR NUMBER RBR')
    def identifier(self, p):
        self.lines = p.lineno
        a = get_table(p.PIDENTIFIER, get_variable(p.NUMBER,p.lineno), p.lineno)
        return a

    def error(self, p):
        raise Exception("Syntax error in grammar\n"
                        f"Line {p.lineno}")

    def __init__(self) -> None:
        super().__init__()
        self.lines = 0