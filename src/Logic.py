from collections import deque

free_memory = 0
declared_variables = {}
registers = {}
additional_numbers = []
last_register_copy = deque()
from Models import *

e_register = Register("e")
f_register = Register("f")


def declare_variables(pidentifier, start=None, end=None):
    global declared_variables
    if start is None:
        if pidentifier in declared_variables:
            raise Exception("Variable " + pidentifier + " already exist!!!")
        declared_variables[pidentifier] = Variable(pidentifier, generate_memory_number(False))
    else:
        if pidentifier in declared_variables:
            raise Exception("Table " + pidentifier + " already exist!!!")
        declared_variables[pidentifier] = Table(pidentifier, start, end, generate_memory_number(True, start, end))


def generate_memory_number(is_table, start=None, end=None):
    global free_memory
    if is_table:
        a = free_memory
        free_memory += end - start + 1
        return a
    else:
        a = free_memory
        free_memory += 1
        return a


def initialize_registers():
    global registers
    registers["a"] = Register("a")
    registers["b"] = Register("b")
    registers["c"] = Register("c")
    registers["d"] = Register("d")
    # registers["e"] = Register("e")


# not for table
# return Variable/Number/Special
def get_variable(pidentifier):
    if pidentifier in declared_variables:
        if isinstance(declared_variables[pidentifier], Table):
            raise Exception("No index parameter for table " + pidentifier)
        return declared_variables[pidentifier]
    else:
        if isinstance(pidentifier, int):
            return Number(pidentifier, pidentifier, None)
        raise Exception("Variable " + pidentifier + " not declared before")


# for tables
# return TableValue
def get_table(pidentifier, move):
    return TableValue(pidentifier, move)


# return Register,[string],[LostRegister]
def get_free_register():
    possible_registers = [register for register in registers.values() if not register.is_blocked]
    # restarted
    for reg in possible_registers:
        if reg.type is RegisterType.is_restarted:
            return reg, [], []
    # unknown
    for reg in possible_registers:
        if reg.type is RegisterType.is_unknown:
            return reg, [], []
    # variable (no need to save)
    for reg in possible_registers:
        if reg.type is RegisterType.is_variable:
            return reg, [], [LostRegister(reg, reg.variable, reg.type)]
    # save variable
    for reg in possible_registers:
        if reg.type is RegisterType.is_to_save:
            # saving
            return reg, save_register(reg), [LostRegister(reg, reg.variable, reg.type)]

    raise Exception("Could not find free register")


# return [string]
def generate_number(number, register):
    string = []
    if number > 0:
        while number > 0:
            if number == 1:
                string = [f"INC {register.name}"] + string
            else:
                if number % 2 == 1:
                    string = [f"SHL {register.name}", f"INC {register.name}"] + string
                else:
                    string = [f"SHL {register.name}"] + string
            number = int(number / 2)
        if register.type is not RegisterType.is_restarted:
            string = [f"RESET {register.name}"] + string
        else:
            register.type = RegisterType.is_unknown
    else:
        if register.type is not RegisterType.is_restarted:
            string = [f"RESET {register.name}"] + string
        register.type = RegisterType.is_restarted
    return string


# return [string]
def save_register(register):
    string = []
    variable = register.variable
    register.type = RegisterType.is_variable
    if variable.memory_address is not None:
        print(f"Saving {register.variable.name} to {register.variable.memory_address}")
        string += generate_number(variable.memory_address, f_register)
        string += [f"STORE {register.name} {f_register.name}"]
        return string
    elif isinstance(variable, TableValue):
        print(f"Saving {register.variable.name} {register.variable.move.name}")
        reg, string, lost_register = get_table_address_of_variable(variable)
        string.append(f"STORE {register.name} {reg.name}")
        return string


# return boolean
def are_variables_same(var1, var2):
    try:
        if var1.name == var2.name:
            if isinstance(var1, TableValue):
                return are_variables_same(var1.move, var2.move)
            else:
                return True
    except:
        return False


# return Register, [string], [LostRegister]
def get_table_address_of_variable(variable):
    if variable.memory_address is not None:
        return f_register, generate_number(variable.memory_address, f_register), []
    for register in registers.values():
        if register.variable is not None and are_variables_same(register.variable, variable.move):
            if are_variables_same(variable.move, register.variable):
                move = register
                string = []
                lost_register = []
                break
    else:
        string = load_normal_variable_to_register(variable.move, e_register)
        move = e_register
        lost_register = []
    string += generate_number(variable.table.memory_address, f_register)
    string.append(f"ADD {f_register.name} {move.name}")
    if variable.table.start > 0:
        string += generate_number(variable.table.start, e_register)
        string.append(f"SUB {f_register.name} {e_register.name}")
    return f_register, string, lost_register


# return Register,[string],[LostRegister]
def load_variable_to_register(variable):
    for register in registers.values():
        if register.variable is not None:
            if variable.name == register.variable.name:
                if isinstance(variable, TableValue):
                    if variable.move.name == register.variable.move.name:
                        return register, [], []
                else:
                    return register, [], []

    a, b, c = get_free_register()
    b1, c1 = load_variable_to_specific_register(variable, a)
    return a, b + b1, c + c1
    # a.variable = variable
    # a.type = RegisterType.is_variable
    # if isinstance(variable, TableValue):
    #     a1, b1, c1 = get_table_address_of_variable(variable)
    #     b1.append(f"LOAD {a.name} {a1.name}")
    #     return a, b + b1, c + c1
    # else:
    #
    #     return a, b + load_normal_variable_to_register(variable, a), c


# return [string], [LostRegs]
def load_variable_to_specific_register(variable, chosen_reg):
    pom_reg = None
    string = []
    for register in registers.values():
        if are_variables_same(register.variable, variable):
            pom_reg = register
            break
    if pom_reg is not None:
        if chosen_reg.type == RegisterType.is_to_save:
            string += save_register(chosen_reg)
        string += reset_register(chosen_reg)
        string.append(f"ADD {chosen_reg.name} {pom_reg.name}")
        chosen_reg.variable = variable
        return string, []
    else:
        chosen_reg.variable = variable
        chosen_reg.type = RegisterType.is_variable
        if isinstance(variable, TableValue):
            a1, b1, c1 = get_table_address_of_variable(variable)
            b1.append(f"LOAD {chosen_reg.name} {a1.name}")
            return string + b1, c1
        else:
            return string + load_normal_variable_to_register(variable, chosen_reg), []


# return [string]
def load_normal_variable_to_register(variable, register):
    string = []
    if variable.memory_address is not None:
        result = generate_number(variable.memory_address, f_register)
        string.append(f"LOAD {register.name} {f_register.name}")
        return result + string
    else:
        return generate_number(variable.value, register)


# return [string]
def reset_register(register):
    if register.type is RegisterType.is_restarted:
        return []
    else:
        register.value = None
        register.type = RegisterType.is_restarted
        return [f"RESET {register.name}"]


# return [string],[LostRegister]
def assign_value(identifier, info):
    old_reg = info[0]
    old_string = info[1]
    lost_reg = info[2]
    if are_variables_same(identifier, old_reg.variable):
        print(f"Same variables: {identifier.name}, skip")
        return old_string, lost_reg
    if old_reg.type is RegisterType.is_to_save:
        old_string += save_register(old_reg)
        lost_reg.append(LostRegister(old_reg, old_reg.variable, old_reg.type))

        # usuwanie pozostałości z rejestru
    for register in registers.values():
        if register.variable is not None:
            if register.variable.name == identifier.name:
                if isinstance(register.variable, TableValue):
                    if register.variable.move.name == identifier.move.name:
                        print(
                            f"Czyszczenie rejestru {register.name} z pozostałości po {identifier.name} {identifier.move.name}")
                        lost_reg.append(LostRegister(register, register.variable, old_reg.type))
                        register.type = RegisterType.is_unknown
                        register.variable = None
                        break
                else:
                    print(f"Czyszczenie rejestru {register.name} z pozostałości po {identifier.name}")
                    lost_reg.append(LostRegister(register, register.variable, old_reg.type))
                    register.type = RegisterType.is_unknown
                    register.variable = None
                    break
    old_reg.type = RegisterType.is_to_save
    old_reg.variable = identifier
    identifier.assigned = True
    return old_string, lost_reg


def concatenate_commands(command1, command2):
    strings = command1[0] + command2[0]
    lost_regs = command1[1] + command2[1]
    return strings, lost_regs


# return Register,[string], [LostRegister]
def load_memory_address_of_variable(variable):
    if variable.memory_address is not None:
        for register in registers.values():
            if isinstance(register, Number):
                if register.value == variable.memory_address:
                    return register, [], []
        return f_register, generate_number(variable.memory_address, f_register), []
    if isinstance(variable, TableValue):
        return get_table_address_of_variable(variable)
    if isinstance(variable, Number):
        global free_memory

        print(f"Saving number {variable.name} in {free_memory}")
        variable.memory_address = free_memory
        free_memory += 1
        declared_variables[variable.name] = variable
        additional_numbers.append(variable)
        return load_memory_address_of_variable(variable)
    raise Exception("Unknown memory value!!!")


# return [string], [LostRegister]
def write_value(variable):
    check_is_assigned(variable)
    string = []
    lost_register = []
    # check if is variable not saved
    pom = None
    for register in registers.values():
        if register.variable is not None:
            if variable.name == register.variable.name:
                if isinstance(variable, TableValue):
                    if variable.move.name == register.variable.move.name:
                        pom = register
                        break
                else:
                    pom = register
                    break

    if pom is not None and pom.type is RegisterType.is_to_save:
        # lost_register.append(LostRegister(pom,pom.variable))
        # string += reset_register(pom)
        string += save_register(pom)
        string.append(f"PUT {f_register.name}")
        return string, []
    a, b, c = load_memory_address_of_variable(variable)
    b.append(f"PUT {a.name}")
    return string + b, lost_register + c


def check_is_assigned(variable):
    if not variable.assigned:
        raise Exception(f"Value {variable.name} not assign before use")


def generate_additional_numbers():
    global additional_numbers
    try:
        memory = additional_numbers[0].memory_address
        string = [f"RESET {f_register.name}"]
        f_register.type = RegisterType.is_restarted
    except:
        return []
    string += generate_number(memory, f_register)
    for i in range(len(additional_numbers)):
        string += generate_number(additional_numbers[i].value, e_register)
        string.append(f"STORE {e_register.name} {f_register.name}")
        if i < len(additional_numbers) - 1:
            string.append(f"INC {f_register.name}")
    return string


# return Register,[string], [LostRegister]
def add_variables(info1, variable2):
    reg1 = info1[0]
    string = info1[1]
    lost_regs = info1[2]
    if reg1.type == RegisterType.is_to_save:
        string += save_register(reg1)
    if are_variables_same(info1[0].variable, variable2):
        string.append(f"SHL {reg1.name}")
    elif variable2.name == "1":
        string.append(f"INC {reg1.name}")
    elif variable2.name == "0":
        pass
    else:
        a, b, c = load_variable_to_register(variable2)
        string += b
        lost_regs += c
        string.append(f"ADD {reg1.name} {a.name}")
    reg1.variable = None
    reg1.is_blocked = False
    return reg1, string, lost_regs


def sub_variables(info1, variable2):
    reg1 = info1[0]
    string = info1[1]
    lost_regs = info1[2]
    if reg1.type == RegisterType.is_to_save:
        string += save_register(reg1)
    elif are_variables_same(info1[0].variable, variable2):
        string.append(f"RESET {reg1.name}")
    elif variable2.name == "1":
        string.append(f"DEC {reg1.name}")
    elif variable2.name == "0":
        pass
    else:
        a, b, c = load_variable_to_register(variable2)
        string += b
        lost_regs += c
        string.append(f"SUB {reg1.name} {a.name}")
    reg1.variable = None
    reg1.is_blocked = False
    return reg1, string, lost_regs


# TODO make optimizations
def mul_variables(info1, variable2):
    r1 = info1[0]
    string = info1[1]
    lost_regs = info1[2]
    if r1.type == RegisterType.is_to_save:
        string += save_register(r1)
    if variable2.name == "0" or variable2.name == "0":
        string.append(f"RESET {r1.name}")
    elif isinstance(r1, Number) and isinstance(variable2, Number):
        string += generate_number(int(r1.value * variable2.value), r1)
    else:
        r2, b, c = load_variable_to_register(variable2)
        r2.is_blocked = True
        result, b2, c3 = get_free_register()
        string += b + b2
        lost_regs += c + c3
        string += [
            f"RESET {result.name}",
            f"ADD {result.name} {r2.name}",
            f"SUB {result.name} {r1.name}",
            f"JZERO {result.name} 10",
            f"RESET {result.name}",
            f"JODD {r1.name} 2",
            f"JUMP 2",
            f"ADD {result.name} {r2.name}",
            f"SHL {r2.name}",
            f"SHR {r1.name}",
            f"JZERO {r1.name} 2",
            f"JUMP -6",
            f"JUMP 8",
            f"JODD {r2.name} 2",
            f"JUMP 2",
            f"ADD {result.name} {r1.name}",
            f"SHL {r1.name}",
            f"SHR {r2.name}",
            f"JZERO {r2.name} 2",
            f"JUMP -6",
        ]
        r2.is_blocked = False
        r1.is_blocked = False
        r1.variable = None
        r1.type = RegisterType.is_unknown
        return result, string, lost_regs
    r1.is_blocked = False
    r1.variable = None
    return r1, string, lost_regs


def div_variables(info1, variable2):
    r1 = info1[0]
    string = info1[1]
    lost_regs = info1[2]
    if r1.type == RegisterType.is_to_save:
        string += save_register(r1)
    if are_variables_same(info1[0].variable, variable2):
        string.append(f"RESET {r1.name}")
        string.append(f"INC {r1.name}")
    elif isinstance(r1, Number) and isinstance(variable2, Number):
        string += generate_number(int(r1.value / variable2.value), r1)
    else:
        r2, b, c = load_variable_to_register(variable2)
        r2.is_blocked = True
        result, b2, c3 = get_free_register()
        string += b + b2
        lost_regs += c + c3
        string += [
            f"RESET {result.name}",
            f"JZERO {r2.name} 26",
            f"RESET {e_register.name}",
            f"ADD {e_register.name} {r2.name}",
            f"RESET {result.name}",
            f"ADD {result.name} {e_register.name}",
            f"SUB {result.name} {r1.name}",
            f"JZERO {result.name} 2",
            f"JUMP 3",
            f"SHL {e_register.name}",
            f"JUMP -6",
            f"RESET {result.name}",
            f"RESET {f_register.name}",
            f"ADD {f_register.name} {e_register.name}",
            f"SUB {f_register.name} {r1.name}",
            f"JZERO {f_register.name} 4",
            f"SHL {result.name}",
            f"SHR {e_register.name}",
            f"JUMP 5",
            f"SHL {result.name}",
            f"INC {result.name}",
            f"SUB {r1.name} {e_register.name}",
            f"SHR {e_register.name}",
            f"RESET {f_register.name}",
            f"ADD {f_register.name} {r2.name}",
            f"SUB {f_register.name} {e_register.name}",
            f"JZERO {f_register.name} -14"
        ]
        r2.is_blocked = False
        r1.is_blocked = False
        r1.variable = None
        r1.type = RegisterType.is_unknown
        return result, string, lost_regs
    r1.is_blocked = False
    r1.variable = None
    return r1, string, lost_regs


def mod_variables(info1, variable2):
    r1 = info1[0]
    string = info1[1]
    lost_regs = info1[2]
    if r1.type == RegisterType.is_to_save:
        string += save_register(r1)
    if variable2.name == "0" or variable2.name == "0":
        string.append(f"RESET {r1.name}")
    elif are_variables_same(r1.variable, variable2):
        string.append(f"RESET {r1.name}")
    elif isinstance(r1.variable, Number) and isinstance(variable2, Number):
        if r1.variable.value < variable2.value:
            pass
        else:
            string += generate_number(r1.variable.value % variable2.value, r1)
    else:
        r2, b, c = load_variable_to_register(variable2)
        r2.is_blocked = True
        result, b2, c3 = get_free_register()
        string += b + b2
        lost_regs += c + c3
        string += [
            f"JZERO  {r2.name} 28",
            f"JZERO  {r2.name} 26",
            f"RESET {e_register.name}",
            f"ADD {e_register.name}  {r2.name}",
            f"RESET  {result.name}",
            f"ADD  {result.name} {e_register.name}",
            f"SUB  {result.name}  {r1.name}",
            f"JZERO  {result.name} 2",
            f"JUMP 3",
            f"SHL {e_register.name}",
            f"JUMP -6",
            f"RESET  {result.name}",
            f"RESET {f_register.name}",
            f"ADD {f_register.name} {e_register.name}",
            f"SUB {f_register.name}  {r1.name}",
            f"JZERO {f_register.name} 4",
            f"SHL  {result.name}",
            f"SHR {e_register.name}",
            f"JUMP 5",
            f"SHL  {result.name}",
            f"INC  {result.name}",
            f"SUB  {r1.name} {e_register.name}",
            f"SHR {e_register.name}",
            f"RESET {f_register.name}",
            f"ADD {f_register.name}  {r2.name}",
            f"SUB {f_register.name} {e_register.name}",
            f"JZERO {f_register.name} -14",
            f"JUMP 2",
            f"RESET  {r1.name}",
            f"RESET  {result.name}",
            f"ADD  {result.name}  {r1.name}"
        ]
        r2.is_blocked = False
        r1.is_blocked = False
        r1.variable = None
        r1.type = RegisterType.is_unknown
        return result, string, lost_regs
    r1.is_blocked = False
    r1.variable = None
    return r1, string, lost_regs


def read_variable(variable):
    for register in registers.values():
        if are_variables_same(register, variable):
            register.variable = None
            register.type = RegisterType.is_unknown
    a, b, c = load_memory_address_of_variable(variable)
    b.append(f"GET {a.name}")
    return b, c


def copy_of_registers():
    reg_copy = []
    for register in registers.values():
        reg_copy.append(LostRegister(register, register.variable, register.type))
    global last_register_copy
    result = [reg_copy, LostRegister(e_register, e_register.variable, e_register.type),
              LostRegister(f_register, f_register.variable, f_register.type)]
    last_register_copy.append(result)
    return result


# return [string] which need to be added to last commands
def load_registers():
    last_copy = last_register_copy.pop()
    last_register_copy.append(last_copy)
    string = []
    lostRegs = []
    for x in last_copy[0] + [last_copy[1], last_copy[2]]:
        real_reg = x.register
        was_type = x.register_type
        was_variable = x.variable
        if was_type == RegisterType.is_variable:
            if are_variables_same(was_variable, real_reg.variable):
                if real_reg.type == RegisterType.is_to_save:
                    string += save_register(real_reg)
            else:
                z = load_variable_to_specific_register(was_variable, real_reg)
                string += z[0]
                lostRegs += z[1]
        elif was_type == RegisterType.is_to_save:
            if are_variables_same(was_variable, real_reg.variable):
                if real_reg.type == RegisterType.is_to_save:
                    pass
            else:
                if real_reg.type == RegisterType.is_to_save:
                    string += save_register(real_reg)
                z = load_variable_to_specific_register(was_variable, real_reg)
                string += z[0]
                lostRegs += z[1]
                real_reg.type = RegisterType.is_to_save

    for x in last_copy[0] + [last_copy[1], last_copy[2]]:
        real_reg = x.register
        was_type = x.register_type
        if was_type == RegisterType.is_unknown:
            if real_reg.type == RegisterType.is_to_save:
                string += save_register(real_reg)
            real_reg.variable = None
            real_reg.type = RegisterType.is_unknown
        elif was_type == RegisterType.is_restarted:
            if real_reg.type == RegisterType.is_to_save:
                string += save_register(real_reg)
                string.append(f"RESET {real_reg.name}")
            real_reg.variable = None
            real_reg.type = RegisterType.is_restarted
    return string, lostRegs


# return [string],[LostRegs]
def condition_equal(variable1, variable2, commands_true, commands_false, normal_build=True):
    if isinstance(variable1, Number) and isinstance(variable2, Number):
        if variable1.value == variable2.value:
            return commands_true
        else:
            return commands_false
    else:
        reg1, s1, c1 = load_variable_to_register(variable1)
        if reg1.type == RegisterType.is_to_save:
            s1 += save_register(reg1)
        reg2, s2, c2 = load_variable_to_register(variable2)
        string = s1 + s2
        if normal_build:
            move_true = 2
            move_false1 = 3 + len(commands_true)
            move_false2 = len(commands_true)

        string += [
            f"INC {reg1.name}",
            f"SUB {reg1.name} {reg2.name}",
            f"JZERO {reg1.name} {move_false1}",
            f"DEC {reg1.name}",
            f"JZERO {reg1.name} {move_true}",
            f"JUMP {move_false2}"
        ]
        reg1.variable = None
        reg1.type = RegisterType.is_unknown
        return None
