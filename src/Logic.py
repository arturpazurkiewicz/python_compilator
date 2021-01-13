free_memory = 0
declared_variables = {}
registers = {}
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
    # registers["b"] = Register("b")
    # registers["c"] = Register("c")
    # registers["d"] = Register("d")
    # registers["e"] = Register("e")


# not for table
# return Variable/Number/Special
def get_variable(pidentifier):
    if pidentifier in declared_variables:
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
            return reg, [reg], []
    # save variable
    for reg in possible_registers:
        if reg.type is RegisterType.is_to_save:
            # saving
            return reg, save_register(reg), [LostRegister(reg, reg.variable)]

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
    print(f"Saving {register.variable.name}")
    if variable.memory_address is not None:
        string += generate_number(variable.memory_address, f_register)
        string += [f"STORE {register.name} {f_register.name}"]
        return string
    elif isinstance(variable, TableValue):
        print("Ojojoj")


# return boolean
def are_variables_same(var1, var2):
    if var1.name == var2.name:
        if isinstance(var1, TableValue):
            return are_variables_same(var1.move, var2.move)
        else:
            return True


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
    string = []

    result = get_free_register()
    new_reg = result[0]
    if isinstance(variable, TableValue):
        # a = generate_number(variable.memory_address, f_register)
        for register in registers.values():
            if register.variable is not None:
                if register.variable.move.name == register.variable.name:
                    string += reset_register(new_reg)
                    string.append(f"ADD {new_reg.name} {register.name}")
                    break
        else:
            string += load_normal_variable_to_register(variable.move, new_reg)
        string += generate_number(variable.memory_address, f_register)
        string.append(f"ADD {new_reg.name} {f_register.name}")
        string.append(f"LOAD {new_reg.name} {f_register.name}")
        # result[1] += string
        return result[0], result[1] + string, result[2]
    else:
        return result[0], result[1] + load_normal_variable_to_register(variable, new_reg), result[2]


# return [string]
def load_normal_variable_to_register(variable, register):
    string = []
    if variable.memory_address is not None:
        result = generate_number(variable.memory_address, f_register)
        string.append(f"LOAD {register.name} {variable.memory_address}")
        return result + string
    else:
        return generate_number(variable.value, register)


# return [string]
def reset_register(register):
    if register.type is RegisterType.is_restarted:
        return []
    else:
        return [f"RESET {register.name}"]


# return [string],[LostRegister]
def assign_value(identifier, info):
    old_reg = info[0]
    old_string = info[1]
    old_lost = info[2]
    lost_reg = info[2]
    if old_reg.type is RegisterType.is_to_save:
        old_string += save_register(old_reg)
        lost_reg.append(LostRegister(old_reg, old_reg.variable))

        # usuwanie pozostałości z rejestru
    for register in registers.values():
        if register.variable is not None:
            if register.variable.name == identifier.name:
                if isinstance(register.variable, TableValue):
                    if register.variable.move.name == identifier.move.name:
                        print(
                            f"Czyszczenie rejestru {register.name} z pozostałości po {identifier.name} {identifier.move.name}")
                        lost_reg.append(LostRegister(register, register.variable))
                        register.type = RegisterType.is_unknown
                        register.variable = None
                        break
                else:
                    print(f"Czyszczenie rejestru {register.name} z pozostałości po {identifier.name}")
                    lost_reg.append(LostRegister(register, register.variable))
                    register.type = RegisterType.is_unknown
                    register.variable = None
                    break
    old_reg.type = RegisterType.is_to_save
    old_reg.variable = identifier
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
    string = []
    if isinstance(variable, TableValue):
        for register in registers.values():
            if register.variable is not None:
                if register.variable.move.name == register.variable.name:
                    string += reset_register(new_reg)
                    string.append(f"ADD {new_reg.name} {register.name}")
                    break
        else:
            string += load_normal_variable_to_register(variable.move, new_reg)
    raise Exception("Unknown memory value!!!")


# return Register,[string], [LostRegister]
def write_value(variable):
    return load_memory_address_of_variable(variable)
