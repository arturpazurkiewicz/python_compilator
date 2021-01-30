import copy
import math
from collections import deque

free_memory = 0
declared_variables = {}
registers = {}
additional_numbers = []
last_register_copy = deque()
for_optimization = False
from Models import *

e_register = Register("e")
f_register = Register("f")


def declare_variables(pidentifier, start=None, end=None, line=-1):
    global declared_variables
    if start is None:
        if pidentifier in declared_variables:
            raise Exception("Variable " + pidentifier + " already exist!!!"
                                                        f"\nLine {line}")
        declared_variables[pidentifier] = Variable(pidentifier, generate_memory_number(False))
    else:
        if pidentifier in declared_variables:
            raise Exception("Table " + pidentifier + " already exist!!!"
                                                     f"\nLine {line}")
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
    global e_register
    global f_register
    e_register = Register("e")
    f_register = Register("f")
    # registers["e"] = Register("e")


# not for table
# return Variable/Number/Special
def get_variable(pidentifier, line):
    if pidentifier in declared_variables:
        if isinstance(declared_variables[pidentifier], Table):
            raise Exception("No index parameter for table " + pidentifier + f"\nLine {line}")
        return declared_variables[pidentifier]
    else:
        if isinstance(pidentifier, int):
            return Number(pidentifier, pidentifier, None)
        raise Exception("Variable " + pidentifier + " not declared before" + f"\nLine {line}")


# for tables
# return TableValue
def get_table(pidentifier, move, line):
    check_is_assigned(move, line)
    if not isinstance(declared_variables[pidentifier], Table):
        raise Exception(f"{pidentifier} is not a table" + f"\nLine {line}")
    return TableValue(pidentifier, move, line)


# return Register,[string]
def get_free_register():
    possible_registers = [register for register in registers.values() if not register.is_blocked]
    # restarted
    for reg in possible_registers:
        if reg.type is RegisterType.is_restarted:
            return reg, []
    # unknown
    for reg in possible_registers:
        if reg.type is RegisterType.is_unknown:
            return reg, []
    # variable (no need to save)
    for reg in possible_registers:
        if reg.type is RegisterType.is_variable:
            return reg, []
    # save variable, not iterator
    for reg in possible_registers:
        if reg.type is RegisterType.is_to_save and not isinstance(reg.variable, ForVariable):
            # saving
            return reg, save_register(reg)
    # save iterator
    for reg in possible_registers:
        if reg.type is RegisterType.is_to_save:
            # saving
            return reg, save_register(reg)


# return [string]
def generate_number(number, register):
    all_possibilities = [generate_classic(number, register)]
    max = all_possibilities[0][0]
    all_possibilities += generate_from_registers(number, register, max)
    string = min(all_possibilities)[1]
    # print(f"Było {register.variable}, jest {number}, rejestr {register.name}")
    register.variable = Number(number, number, None)
    register.type = RegisterType.is_variable

    return string


def generate_classic(number, register):
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
            number = number >> 1
        if register.type is not RegisterType.is_restarted:
            string = [f"RESET {register.name}"] + string
        else:
            register.type = RegisterType.is_unknown
    else:
        if register.type is not RegisterType.is_restarted:
            string = [f"RESET {register.name}"] + string
        register.type = RegisterType.is_restarted
    return [len(string), string]


def generate_from_registers(number, register, max):
    result = []
    if isinstance(register.variable, Number):
        for reg in list(registers.values()) + [e_register, f_register]:
            if isinstance(reg.variable, Number) and reg.type is RegisterType.is_variable:
                string = []
                base = reg.variable.value
                if reg == register:
                    # same register
                    move = number - base
                    if abs(move) < max:
                        if move > 0:
                            string += [f"INC {reg.name}"] * move
                        if move < 0:
                            string += [f"DEC {reg.name}"] * -move
                        result.append([abs(move), string])
                    continue
                # different registers
                move = number - (register.variable.value + reg.variable.value)
                if abs(move) < max:
                    string = [f"ADD {register.name} {reg.name}"]
                    if move > 0:
                        string += [f"INC {register.name}"] * move
                    if move < 0:
                        string += [f"DEC {register.name}"] * -move
                    result.append([5 + abs(move), string])
                if abs(move) < max:
                    if register.variable.value - reg.variable.value > 0:
                        string = [f"SUB {register.name} {reg.name}"]
                        if move > 0:
                            string += [f"INC {register.name}"] * move
                        if move < 0:
                            string += [f"DEC {register.name}"] * -move
                        result.append([5 + abs(move), string])

    return result


# return [string]
def save_register(register):
    if register.type is RegisterType.is_to_save:
        string = []
        variable = register.variable
        register.type = RegisterType.is_variable
        if variable.memory_address is not None:
            # print(f"Saving {register.variable.name} to {register.variable.memory_address}")
            string += generate_number(variable.memory_address, f_register)
            string += [f"STORE {register.name} {f_register.name}"]
            return string
        elif isinstance(variable, TableValue):
            # print(f"Saving {register.variable.name} with move {register.variable.move.name}")
            reg, string = get_table_address_of_variable(variable)
            string.append(f"STORE {register.name} {reg.name}")
            return string
    return []


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


# return Register, [string]
def get_table_address_of_variable(variable):
    # for register in list(registers.values()) + [e_register,f_register]:
    #     if isinstance(register.variable,TableValueMemory) \
    #             and variable.table == register.variable.table \
    #             and variable.move.name == register.variable.move.name:
    #         return register,[]
    if variable.memory_address is not None:
        return f_register, generate_number(variable.memory_address, f_register)
    for register in registers.values():
        if register.variable is not None and are_variables_same(register.variable, variable.move):
            if are_variables_same(variable.move, register.variable):
                move = register
                string = []
                break
    else:
        string = load_normal_variable_to_register(variable.move, e_register)
        move = e_register
        # print("Found move!!!")
    string += generate_number(variable.table.memory_address, f_register)
    string.append(f"ADD {f_register.name} {move.name}")
    # fix
    f_register.type = RegisterType.is_unknown
    f_register.variable = None
    if variable.table.start > 0:
        string += generate_number(variable.table.start, e_register)
        string.append(f"SUB {f_register.name} {e_register.name}")

    # f_register.variable = TableValueMemory(variable.table, variable.move)
    return f_register, string


# return Register,[string]
def load_variable_to_register(variable):
    for register in registers.values():
        if are_variables_same(variable, register.variable):
            return register, []

    a, b = get_free_register()
    b1 = load_variable_to_specific_register(variable, a)
    return a, b + b1
    # a.variable = variable
    # a.type = RegisterType.is_variable
    # if isinstance(variable, TableValue):
    #     a1, b1, c1 = get_table_address_of_variable(variable)
    #     b1.append(f"LOAD {a.name} {a1.name}")
    #     return a, b + b1, c + c1
    # else:
    #
    #     return a, b + load_normal_variable_to_register(variable, a), c


# return [string]
def load_variable_to_specific_register(variable, chosen_reg):
    pom_reg = None
    string = []
    for register in registers.values():
        if are_variables_same(register.variable, variable):
            pom_reg = register
            break
    if pom_reg is not None:
        if pom_reg == chosen_reg:
            return []
        if chosen_reg.type == RegisterType.is_to_save:
            string += save_register(chosen_reg)
        string += reset_register(chosen_reg)
        string.append(f"ADD {chosen_reg.name} {pom_reg.name}")
        chosen_reg.variable = variable
        return string
    else:

        if isinstance(variable, TableValue):
            chosen_reg.variable = variable
            chosen_reg.type = RegisterType.is_variable
            a1, b1 = get_table_address_of_variable(variable)
            b1.append(f"LOAD {chosen_reg.name} {a1.name}")
            return string + b1
        else:
            string += load_normal_variable_to_register(variable, chosen_reg)
            chosen_reg.variable = variable
            chosen_reg.type = RegisterType.is_variable
            return string


# return [string]
def load_normal_variable_to_register(variable, register):
    string = []
    if variable.memory_address is not None:
        result = generate_number(variable.memory_address, f_register)
        string.append(f"LOAD {register.name} {f_register.name}")
        register.type = RegisterType.is_variable
        register.variable = variable
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


# return [string]
def assign_value(identifier, info, line):
    if isinstance(identifier, ForVariable):
        raise Exception(f"For variable {identifier.name} cannot be modified!!!" + f"\nLine {line}")

    old_reg = info[0]
    old_string = info[1]
    if are_variables_same(identifier, old_reg.variable):
        # print(f"Same variables: {identifier.name}, skip")
        return old_string

    if old_reg.type is RegisterType.is_to_save:
        old_string += save_register(old_reg)

    if isinstance(identifier, TableValue):
        old_reg.variable = None
        old_reg.type = RegisterType.is_unknown
        return change_table_value(identifier, info)
    # usuwanie pozostałości z rejestru
    for register in registers.values():
        if register.variable is not None:
            if register.variable.name == identifier.name:
                # print(f"Czyszczenie rejestru {register.name} z pozostałości po {identifier.name}")
                register.type = RegisterType.is_unknown
                register.variable = None
                break
    old_reg.type = RegisterType.is_to_save
    old_reg.variable = identifier
    identifier.assigned = True
    return old_string


# od razu zapisuje tablicę
# usuwa wszystkie pozostałości po tablicy
def change_table_value(identifier, info):
    old_reg = info[0]
    string = info[1]
    # if old_reg.type is RegisterType.is_to_save:
    #     string += save_register(old_reg)
    if isinstance(identifier, Number):
        for register in registers.values():
            if register.variable is not None:
                if register.variable.name == identifier.name:
                    if not isinstance(register.variable.move, Number):
                        if register.type == RegisterType.is_to_save:
                            string += save_register(register)
                        register.type = RegisterType.is_unknown
                        register.variable = None
    else:
        for register in registers.values():
            if register.variable is not None:
                if register.variable.name == identifier.name:
                    if register.type == RegisterType.is_to_save:
                        string += save_register(register)
                    register.type = RegisterType.is_unknown
                    register.variable = None
    # old_reg.type = RegisterType.is_to_save
    # old_reg.variable = identifier
    # if not isinstance(identifier.move, Number):
    #     string += save_register(old_reg)
    reg, str = get_table_address_of_variable(identifier)
    str.append(f"STORE {old_reg.name} {reg.name}")
    return string + str


def concatenate_commands(command1, command2):
    strings = command1 + command2
    return strings


# return Register,[string]
def load_memory_address_of_variable(variable):
    if variable.memory_address is not None:
        for register in registers.values():
            if isinstance(register, Number):
                if register.value == variable.memory_address:
                    return register, []
        return f_register, generate_number(variable.memory_address, f_register)
    if isinstance(variable, TableValue):
        return get_table_address_of_variable(variable)
    if isinstance(variable, Number):
        global free_memory

        # print(f"Saving number {variable.name} in {free_memory}")
        variable.memory_address = free_memory
        free_memory += 1
        declared_variables[variable.name] = variable
        additional_numbers.append(variable)
        return load_memory_address_of_variable(variable)
    raise Exception("Unknown memory value!!!")


# return [string]
def write_value(variable, line):
    check_is_assigned(variable, line)
    string = []
    # check if is variable not saved
    pom = None
    for register in registers.values():
        if register.variable is not None:
            if variable.name == register.variable.name:
                if isinstance(variable, TableValue):
                    if register.type == RegisterType.is_to_save:
                        string += save_register(register)
                else:
                    pom = register
                    break

    if pom is not None and pom.type is RegisterType.is_to_save:
        # lost_register.append(LostRegister(pom,pom.variable))
        # string += reset_register(pom)
        string += save_register(pom)
        string.append(f"PUT {f_register.name}")
        return string
    a, b = load_memory_address_of_variable(variable)
    b.append(f"PUT {a.name}")
    return string + b


def check_is_assigned(variable, line):
    if not variable.assigned:
        raise Exception(f"Value {variable.name} not assign before use" + f"\nLine {line}")


def generate_additional_numbers():
    global additional_numbers
    try:
        initialize_registers()
        string = []
    except:
        return []
    for i in range(len(additional_numbers)):
        string += generate_number(additional_numbers[i].memory_address, f_register)
        string += generate_number(additional_numbers[i].value, e_register)
        string.append(f"STORE {e_register.name} {f_register.name}")

    return string


# return Register,[string]
def add_variables(variable1, variable2, assigned_to, line):
    check_is_assigned(variable1, line)
    check_is_assigned(variable2, line)
    if isinstance(variable1, Number) and isinstance(variable2, Number):
        a, b = is_in_register(assigned_to)
        if a:
            return b, generate_number(variable1.value + variable2.value, b)
        else:
            r1, string = get_free_register()
            string += generate_number(variable1.value + variable2.value, r1)
            return r1, string

    if are_variables_same(variable1, variable2):
        r1, string = load_variable_to_register(variable1)
        if not are_variables_same(variable1, assigned_to):
            string += save_register(r1)
        string += [
            f"SHL {r1.name}"
        ]
        r1.type = RegisterType.is_unknown
        r1.variable = None
        return r1, string

    if variable1.name == 0:
        return load_variable_to_register(variable2)
    if variable2.name == 0:
        return load_variable_to_register(variable1)
    if variable1.name == 1:
        r1, string = load_variable_to_register(variable2)
        if not are_variables_same(variable2, assigned_to):
            string += save_register(r1)
        r1.type = RegisterType.is_unknown
        r1.variable = None
        string += [
            f"INC {r1.name}"
        ]
        return r1, string
    if variable2.name == 1:
        r1, string = load_variable_to_register(variable1)
        if not are_variables_same(variable1, assigned_to):
            string += save_register(r1)
        r1.type = RegisterType.is_unknown
        r1.variable = None
        string += [
            f"INC {r1.name}"
        ]
        return r1, string

    if are_variables_same(variable1, assigned_to):
        r1, string = load_variable_to_register(variable1)
        r1.is_blocked = True
        r2, s2 = load_variable_to_register(variable2)
        string += s2
        r1.is_blocked = False
        string.append(f"ADD {r1.name} {r2.name}")
        r1.type = RegisterType.is_unknown
        r1.variable = None
        return r1, string
    elif are_variables_same(variable2, assigned_to):
        r1, string = load_variable_to_register(variable2)
        r1.is_blocked = True
        r2, s2 = load_variable_to_register(variable1)
        string += s2
        r1.is_blocked = False
        string.append(f"ADD {r1.name} {r2.name}")
        r1.type = RegisterType.is_unknown
        r1.variable = None
        return r1, string

    r1, string = load_variable_to_register(variable1)
    r1.is_blocked = True
    r2, s2 = load_variable_to_register(variable2)
    string += s2 + save_register(r1) + [
        f"ADD {r1.name} {r2.name}"
    ]
    r1.is_blocked = False
    r1.type = RegisterType.is_unknown
    r1.variable = None
    return r1, string
    # if are_variables_same(reg1.variable, variable2):
    #     string.append(f"SHL {reg1.name}")
    # elif variable2.name == 1:
    #     string.append(f"INC {reg1.name}")
    # elif variable2.name == 0:
    #     pass
    # else:
    #     a, b = load_variable_to_register(variable2)
    #     string += b
    #     string.append(f"ADD {reg1.name} {a.name}")
    # reg1.variable = None
    # reg1.is_blocked = False
    # return reg1, string


def sub_variables(variable1, variable2, assigned_to, line):
    check_is_assigned(variable1, line)
    check_is_assigned(variable2, line)

    if isinstance(variable1, Number) and isinstance(variable2, Number):
        a, b = is_in_register(assigned_to)
        if a:
            return b, generate_number(variable1.value - variable2.value, b)
        else:
            r1, string = get_free_register()
            string += generate_number(variable1.value - variable2.value, r1)
            return r1, string

    # if reg1.type == RegisterType.is_to_save:
    #     if are_variables_same(reg1.variable, assigned_to):
    #         reg1.type = RegisterType.is_variable
    #     else:
    #         string += save_register(reg1)

    if are_variables_same(variable1, variable2):
        x, r1 = is_in_register(assigned_to)
        if x:
            string = [f"RESET {r1.name}"]
        else:
            r1, string = get_free_register()
            string += [f"RESET {r1.name}"]
        r1.type = RegisterType.is_restarted
        r1.variable = None
        return r1, string

    if are_variables_same(variable1, assigned_to):
        r1, string = load_variable_to_register(variable1)
    else:
        r1, string = load_variable_to_register(variable1)
        string += save_register(r1)

    if variable2.name == 1:
        string.append(f"DEC {r1.name}")
    elif variable2.name == 0:
        pass
    else:
        r1.is_blocked = True
        r2, b = load_variable_to_register(variable2)
        string += b
        string.append(f"SUB {r1.name} {r2.name}")
    r1.variable = None
    r1.type = RegisterType.is_unknown
    r1.is_blocked = False
    return r1, string


# TODO make optimizations
def mul_variables(variable1, variable2, assigned_to, line):
    check_is_assigned(variable1, line)
    check_is_assigned(variable2, line)

    if isinstance(variable1, Number) and isinstance(variable2, Number):
        a, b = is_in_register(assigned_to)
        if a:
            return b, generate_number(variable1.value * variable2.value, b)
        else:
            r1, string = get_free_register()
            string += generate_number(variable1.value * variable2.value, r1)
            return r1, string
    if are_variables_same(variable1, assigned_to):
        r1, string = load_variable_to_register(variable1)
    else:
        r1, string = load_variable_to_register(variable1)
        string += save_register(r1)

    if variable1.name == 0 or variable2.name == 0:
        string.append(f"RESET {r1.name}")
    else:
        r1.is_blocked = True
        r2, b = load_variable_to_register(variable2)

        if r1 == r2:
            # print("Warning, same registers!!!")
            r2, b = get_free_register()
            b += load_variable_to_specific_register(variable2, r2)
        r2.is_blocked = True
        string += b
        x, y = is_in_register(assigned_to)
        if x and r2 != y and r1 != y:
            result = y
            result.variable = None
            result.type = RegisterType.is_unknown
        else:
            result, b2 = get_free_register()
            string += b2 + reset_register(result)
        if r2.type == RegisterType.is_to_save and not are_variables_same(r2.variable, assigned_to):
            string += save_register(r2)
        string += [
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
        r2.type = RegisterType.is_unknown
        r2.variable = None
        # print(f"Mnożenie {r1}\n{r2}\n{result}")
        return result, string
    r1.is_blocked = False
    r1.variable = None
    return r1, string


def is_power_of_two(n):
    return (n != 0) and (n & (n - 1) == 0)


def div_variables(variable1, variable2, assigned_to, line):
    check_is_assigned(variable1, line)
    check_is_assigned(variable2, line)
    r1, string = load_variable_to_register(variable1)
    if r1.type == RegisterType.is_to_save:
        if are_variables_same(r1.variable, assigned_to):
            r1.type = RegisterType.is_variable
        else:
            string += save_register(r1)

    if variable2.name == 0 or variable2.name == 0:
        string.append(f"RESET {r1.name}")
    elif isinstance(r1, Number) and isinstance(variable2, Number):
        string += generate_number(int(r1.value / variable2.value), r1)
    elif are_variables_same(variable1, variable2):
        string += [
            f"JZERO {r1.name} 4",
            f"RESET {r1.name}",
            f"INC {r1.name}",
            f"JUMP 2",
            f"RESET {r1.name}"
        ]
    elif isinstance(variable2, Number) and is_power_of_two(variable2.value):
        string += [f"SHR {r1.name}"] * int(math.log2(variable2.value))

    else:
        r1.is_blocked = True
        r2, b = load_variable_to_register(variable2)
        string += b
        r2.is_blocked = True
        x, y = is_in_register(assigned_to)
        if x and r2 != y and r1 != y:
            result = y
            result.variable = None
            result.type = RegisterType.is_unknown
        else:
            result, b2 = get_free_register()
            string += b2
        string += reset_register(result)
        string += [
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
        e_register.type = RegisterType.is_unknown
        e_register.variable = None
        f_register.type = RegisterType.is_unknown
        f_register.variable = None
        r2.is_blocked = False
        r1.is_blocked = False
        r1.variable = None
        r1.type = RegisterType.is_unknown
        return result, string
    r1.is_blocked = False
    r1.variable = None
    r1.type = RegisterType.is_unknown
    return r1, string


# return Bool, register
def is_in_register(variable):
    for register in registers.values():
        if are_variables_same(register.variable, variable):
            return True, register
    return False, None


# variable1 % variable2
def mod_variables(variable1, variable2, assigned_to, line):
    check_is_assigned(variable1, line)
    check_is_assigned(variable2, line)

    if variable1.name == 0 or variable2.name == 0 or are_variables_same(variable1, variable2):
        r1, string = get_free_register()
        string += reset_register(r1)
    elif isinstance(variable1, Number) and isinstance(variable2, Number):
        if variable1.value < variable2.value:
            r1, string = load_variable_to_register(variable1)
        else:
            r1, string = get_free_register()
            string += generate_number(variable1.value % variable2.value, r1)
    elif variable2.name == 2:
        r1, string = load_variable_to_register(variable1)
        if not are_variables_same(r1.variable, assigned_to):
            string += save_register(r1)
        string += [
            f"JODD {r1.name} 3",
            f"RESET {r1.name}",
            f"JUMP 3",
            f"RESET {r1.name}",
            f"INC {r1.name}"
        ]
    else:
        r1, string = load_variable_to_register(variable1)
        r1.is_blocked = True
        r2, b = load_variable_to_register(variable2)
        r2.is_blocked = True
        x, y = is_in_register(assigned_to)
        if x and r2 != y and r1 != y:
            result = y
            string += b
            result.variable = None
            result.type = RegisterType.is_unknown
        else:
            result, b2 = get_free_register()
            string += b + b2
        if not are_variables_same(r1, assigned_to):
            string += save_register(r1)
        string += [
            f"JZERO  {r2.name} 27",
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
        f_register.type = RegisterType.is_unknown
        e_register.type = RegisterType.is_unknown
        f_register.variable = None
        e_register.variable = None
        r2.is_blocked = False
        r1.is_blocked = False
        r1.variable = None
        r1.type = RegisterType.is_unknown
        r2.variable = None
        r2.type = RegisterType.is_unknown
        return result, string
    r1.is_blocked = False
    r1.variable = None
    r1.type = RegisterType.is_unknown
    return r1, string


def read_variable(variable, line):
    if isinstance(variable, ForVariable):
        raise Exception(f"For variable {variable.name} cannot be modified!!!" + f"\nLine {line}")
    for register in registers.values():
        if are_variables_same(register.variable, variable):
            register.variable = None
            register.type = RegisterType.is_unknown
    a, b = load_memory_address_of_variable(variable)
    b.append(f"GET {a.name}")
    variable.assigned = True
    return b


def copy_of_registers():
    reg_copy = []
    for register in registers.values():
        reg_copy.append(LostRegister(register, register.variable, register.type))
    global last_register_copy
    result = (reg_copy,[LostRegister(e_register, e_register.variable, e_register.type),
                         LostRegister(f_register, f_register.variable, f_register.type)])
    last_register_copy.append(result)
    return result


# return [string] which need to be added to last commands
def load_registers():
    last_copy = last_register_copy.pop()
    last_register_copy.append(last_copy)
    string = []
    # print("Loading register")
    for x in last_copy[0]:
        real_reg = x.register
        was_type = x.register_type
        was_variable = x.variable
        if was_type == RegisterType.is_variable:
            if are_variables_same(was_variable, real_reg.variable):
                if real_reg.type == RegisterType.is_to_save:
                    string += save_register(real_reg)
            else:
                if real_reg.type == RegisterType.is_to_save:
                    string += save_register(real_reg)
                z = load_variable_to_specific_register(was_variable, real_reg)
                string += z
        elif was_type == RegisterType.is_to_save:
            if are_variables_same(was_variable, real_reg.variable):
                if real_reg.type == RegisterType.is_to_save:
                    pass
            else:
                if real_reg.type == RegisterType.is_to_save:
                    string += save_register(real_reg)
                z = load_variable_to_specific_register(was_variable, real_reg)
                string += z
                real_reg.type = RegisterType.is_to_save

    for x in last_copy[0]:
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
            else:
                string += reset_register(real_reg)
    for x in last_copy[1]:
        real_reg = x.register
        was_type = x.register_type
        was_variable = x.variable
        if was_type == RegisterType.is_variable:
            string += generate_number(was_variable.value,real_reg)
        if was_type == RegisterType.is_unknown:
            real_reg.variable = None
            real_reg.type = RegisterType.is_unknown
        elif was_type == RegisterType.is_restarted:
            string += reset_register(real_reg)
    return string


# return [string],[LostRegs]
def condition_eq(reg1, reg2, var1, var2, commands_true, commands_false, mode=ConditionMode.is_if, cond_str=None):
    if mode == ConditionMode.is_if:
        if isinstance(reg2.variable, Number) and isinstance(reg1.variable, Number):
            if reg1.variable.value == reg2.variable.value:
                return commands_true
            else:
                return commands_false
        else:
            string = []
            # if reg1.type == RegisterType.is_to_save:
            #     string += save_register(reg1)
            string_true = commands_true
            string_false = commands_false

            if len(string_false) != 0:
                string_true.append(f"JUMP {len(string_false) + 1}")
            string += [
                f"ADD {e_register.name} {reg1.name}",
                f"INC {e_register.name}",
                f"SUB {e_register.name} {reg2.name}",
                f"JZERO {e_register.name} {4 + len(string_true)}",
                f"DEC {e_register.name}",
                f"JZERO {e_register.name} {2}",
                f"JUMP {len(string_true) + 1}"
            ]
            e_register.type = RegisterType.is_unknown
            e_register.variable = None
            return string + string_true + string_false
    elif mode == ConditionMode.is_while:
        if isinstance(var1, Number) and isinstance(var2, Number):
            if var1.value == var2.value:
                print("Warning, infinity loop!!!")
            else:
                return commands_false
        string = []
        # if reg1.type == RegisterType.is_to_save:
        #     string += save_register(reg1)
        e_register.type = RegisterType.is_unknown
        e_register.variable = None
        string = [
            f"ADD {e_register.name} {reg1.name}",
            f"INC {e_register.name}",
            f"SUB {e_register.name} {reg2.name}",
            f"JZERO {e_register.name} {5 + len(commands_true)}",
            f"DEC {e_register.name}",
            f"JZERO {e_register.name} {2}",
            f"JUMP {len(commands_true) + 2}"
        ]
        commands_true.append(f"JUMP {-8 - len(commands_true)}")
        z = string + commands_true
        return z
    elif mode == ConditionMode.is_repeat:
        z = load_registers()
        loader = []
        loader += z
        it = 0
        if len(loader) > 0:
            it = 1
            loader = [f"JUMP {len(loader) + 1}"] + loader
        if variable_was_in_copy(var1):
            commands = [
                f"ADD {e_register.name} {reg1.name}",
                f"INC {e_register.name}",
                f"SUB {e_register.name} {reg2.name}",
                f"JZERO {e_register.name} {-3 - len(commands_true) - len(loader) - len(cond_str) + it}",
                f"DEC {e_register.name}",
                f"JZERO {e_register.name} {2}",
                f"JUMP {- len(commands_true) - 6 - len(loader) - len(cond_str) + it}"
            ]
            e_register.type = RegisterType.is_unknown
            e_register.variable = None
        else:
            commands = [
                f"INC {reg1.name}",
                f"SUB {reg1.name} {reg2.name}",
                f"JZERO {reg1.name} {-2 - len(commands_true) - len(loader) - len(cond_str) + it}",
                f"DEC {reg1.name}",
                f"JZERO {reg1.name} {2}",
                f"JUMP {- len(commands_true) - 5 - len(loader) - len(cond_str) + it}"
            ]
            reg1.variable = None
            reg1.type = RegisterType.is_restarted
        x = loader + commands_true + cond_str + commands + z
        return x


# return [string],[LostRegs]
def condition_neq(reg1, reg2, var1, var2, commands_true, commands_false, mode=ConditionMode.is_if, cond_str=None):
    if mode == ConditionMode.is_if:
        return condition_eq(reg1, reg2, var1, var2, commands_false, commands_true, mode)
    elif mode == ConditionMode.is_while:
        if isinstance(reg2.variable, Number) and isinstance(reg1.variable, Number):
            if reg1.variable.value != reg2.variable.value:
                print("Warning, infinity loop!!!")
            else:
                return commands_false

        string = []
        # if reg1.type == RegisterType.is_to_save:
        #     string += save_register(reg1)
        commands_true += reset_register(e_register)

        string += [
            f"ADD {e_register.name} {reg1.name}",
            f"INC {e_register.name}",
            f"SUB {e_register.name} {reg2.name}",
            f"JZERO {e_register.name} {3}",
            f"DEC {e_register.name}",
            f"JZERO {e_register.name} {2 + len(commands_true)}"
        ]
        commands_true.append(f"JUMP {-7 - len(commands_true)}")
        e_register.type = RegisterType.is_unknown
        e_register.variable = None
        return string + commands_true
    elif mode == ConditionMode.is_repeat:
        z = load_registers()
        loader = []
        loader += z
        it = 0
        if len(loader) > 0:
            it = 1
            loader = [f"JUMP {len(loader) + 1}"] + loader
        if variable_was_in_copy(var1):
            commands = [
                f"ADD {e_register.name} {reg1.name}",
                f"INC {e_register.name}",
                f"SUB {e_register.name} {reg2.name}",
                f"JZERO {e_register.name} {3}",
                f"DEC {e_register.name}",
                f"JZERO {e_register.name} {- len(commands_true) - 5 - len(loader) - len(cond_str) + it}"
            ]
            e_register.type = RegisterType.is_unknown
            e_register.variable = None
        else:
            commands = [
                f"INC {reg1.name}",
                f"SUB {reg1.name} {reg2.name}",
                f"JZERO {reg1.name} {3}",
                f"DEC {reg1.name}",
                f"JZERO {reg1.name} {- len(commands_true) - 4 - len(loader) - len(cond_str) + it}"
            ]
            reg1.variable = None
            reg1.type = RegisterType.is_restarted
        return loader + commands_true + cond_str + commands + z


def condition_lgtr(reg1, reg2, var1, var2, commands_true, commands_false, mode=ConditionMode.is_if, cond_str=None):
    if mode == ConditionMode.is_if:
        if isinstance(var1, Number) and isinstance(var2, Number):
            if var1.value > var2.value:
                return commands_true
            else:
                return commands_false
        else:
            string = []
            # if reg1.type == RegisterType.is_to_save:
            #     string += save_register(reg1)
            string_true = commands_true
            string_false = commands_false

            if len(string_false) != 0:
                string_true.append(f"JUMP {len(string_false) + 1}")
            move_false1 = 1 + len(string_true)

            string += [
                f"ADD {e_register.name} {reg1.name}",
                f"SUB {e_register.name} {reg2.name}",
                f"JZERO {e_register.name} {move_false1}",
            ]
            e_register.type = RegisterType.is_unknown
            e_register.variable = None
        return string + string_true + string_false
    elif mode == ConditionMode.is_while:
        if isinstance(reg2.variable, Number) and isinstance(reg1.variable, Number):
            if reg1.variable.value > reg2.variable.value:
                print("Warning, infinity loop!!!")
            else:
                return commands_false
        string = []
        # if reg1.type == RegisterType.is_to_save:
        #     string += save_register(reg1)
        commands_true += reset_register(e_register)
        e_register.type = RegisterType.is_unknown
        e_register.variable = None
        move_false1 = 2 + len(commands_true)

        string += [
            f"ADD {e_register.name} {reg1.name}",
            f"SUB {e_register.name} {reg2.name}",
            f"JZERO {e_register.name} {move_false1}",
        ]
        commands_true.append(f"JUMP {-3 - len(commands_true)}")
        return string + commands_true
    elif mode == ConditionMode.is_repeat:
        z = load_registers()
        loader = []
        loader += z
        it = 0
        if len(loader) > 0:
            it = 1
            loader = [f"JUMP {len(loader) + 1}"] + loader
        if variable_was_in_copy(var1):
            commands = [
                f"ADD {e_register.name} {reg1.name}",
                f"SUB {e_register.name} {reg2.name}",
                f"JZERO {e_register.name} {- len(commands_true) - 2 - len(loader) - len(cond_str) + it}",
            ]
            e_register.type = RegisterType.is_unknown
            e_register.variable = None
        else:
            # a > b
            commands = [
                f"SUB {reg1.name} {reg2.name}",
                f"JZERO {reg1.name} {- len(commands_true) - 1 - len(loader) - len(cond_str) + it}",
            ]
            reg1.variable = None
            reg1.type = RegisterType.is_restarted

        x = loader + commands_true + cond_str + commands + z
        return x


def condition_leq(reg1, reg2, var1, var2, commands_true, commands_false, mode=ConditionMode.is_if, cond_str=None):
    if mode == ConditionMode.is_if:
        if isinstance(var1, Number) and isinstance(var2, Number):
            if var1.value >= var2.value:
                return commands_true
            else:
                return commands_false
        else:
            string = []
            # if reg1.type == RegisterType.is_to_save:
            #     string += save_register(reg1)
            string_true = commands_true
            string_false = commands_false

            if len(string_false) != 0:
                string_true.append(f"JUMP {len(string_false) + 1}")
            move_false1 = 1 + len(string_true)

            string += [
                f"ADD {e_register.name} {reg2.name}",
                f"SUB {e_register.name} {reg1.name}",
                f"JZERO {e_register.name} 2",
                f"JUMP {move_false1}"
            ]
            e_register.type = RegisterType.is_unknown
            e_register.variable = None
        return string + string_true + string_false
    elif mode == ConditionMode.is_while:
        if isinstance(reg2.variable, Number) and isinstance(reg1.variable, Number):
            if reg1.variable.value >= reg2.variable.value:
                print("Warning, infinity loop!!!")
            else:
                return commands_false
        string = []
        # if reg1.type == RegisterType.is_to_save:
        #     string += save_register(reg1)
        commands_true += reset_register(e_register)
        e_register.type = RegisterType.is_unknown
        e_register.variable = None
        move_false1 = 2 + len(commands_true)

        string += [
            f"ADD {e_register.name} {reg2.name}",
            f"SUB {e_register.name} {reg1.name}",
            f"JZERO {e_register.name} 2",
            f"JUMP {move_false1}"
        ]

        commands_true.append(f"JUMP {-4 - len(commands_true)}")
        reg1.variable = None
        reg1.type = RegisterType.is_unknown
        return string + commands_true
    elif mode == ConditionMode.is_repeat:
        z = load_registers()
        loader = []
        loader += z
        it = 0
        if len(loader) > 0:
            it = 1
            loader = [f"JUMP {len(loader) + 1}"] + loader
        if variable_was_in_copy(var2):
            commands = [
                f"ADD {e_register.name} {reg2.name}",
                f"SUB {e_register.name} {reg1.name}",
                f"JZERO {e_register.name} 2",
                f"JUMP {- len(commands_true) - 3 - len(loader) - len(cond_str) + it}"
            ]
            e_register.type = RegisterType.is_unknown
            e_register.variable = None
        else:
            commands = [
                f"SUB {reg2.name} {reg1.name}",
                f"JZERO {reg2.name} 2",
                f"JUMP {- len(commands_true) - 2 - len(loader) - len(cond_str) + it}"
            ]
            reg2.variable = None
            reg2.type = RegisterType.is_restarted
        #     fixed return
        x = loader + commands_true + cond_str + commands + z
        return x


def condition_rgtr(reg1, reg2, var1, var2, commands_true, commands_false, mode=ConditionMode.is_if, cond_str=None):
    return condition_lgtr(reg2, reg1, var2, var1, commands_true, commands_false, mode, cond_str)


def condition_req(reg1, reg2, var1, var2, commands_true, commands_false, mode=ConditionMode.is_if, cond_str=None):
    return condition_leq(reg2, reg1, var2, var1, commands_true, commands_false, mode, cond_str)


def prepare_condition_result(value0, value1, condition):
    reg1, s1 = load_variable_to_register(value0)
    reg1.is_blocked = True
    reg2, s2 = load_variable_to_register(value1)
    reg1.is_blocked = False
    var1 = reg1.variable
    var2 = reg2.variable
    string = reset_register(e_register)
    e_register.type = RegisterType.is_unknown

    # if condition is condition_req or condition is condition_eq or condition is condition_neq or condition is condition_lgtr:
    #     if reg1.type == RegisterType.is_to_save:
    #         string = save_register(reg1)
    #     reg1.type = RegisterType.is_unknown
    #     reg1.variable = None
    #
    # else:
    #     if reg2.type == RegisterType.is_to_save:
    #         string = save_register(reg2)
    #     reg2.type = RegisterType.is_unknown
    #     reg2.variable = None

    return reg1, reg2, var1, var2, s1 + s2 + string, condition


def remove_copy_of_registers():
    last_register_copy.pop()


# will be using e_register - e_register is restarted but program does not know that
# return Register,RegisterTo, [string], ForVariable
def begin_for(pidentifier, pidentifier_start, pidentifier_end, line):
    if pidentifier in declared_variables:
        raise Exception("Variable " + pidentifier + " already exist!!!" + f"\nLine {line}")
    check_is_assigned(pidentifier_start, line)
    check_is_assigned(pidentifier_end, line)
    new_end = copy.deepcopy(pidentifier_end)
    new_end.name = "^" + pidentifier
    new_end.memory_address = generate_memory_number(False)
    a = ForVariable(pidentifier, pidentifier_start, new_end, generate_memory_number(False))
    declared_variables[pidentifier] = a
    r1, string = load_variable_to_register(pidentifier_start)
    if r1.type is RegisterType.is_to_save:
        string += save_register(r1)
    r1.is_blocked = True
    r1.variable = a
    r1.type = RegisterType.is_to_save
    r2, s2 = load_variable_to_register(pidentifier_end)
    string += s2
    if r2.type is RegisterType.is_to_save:
        string += save_register(r2)
    r2.variable = new_end
    r2.type = RegisterType.is_to_save
    # saving
    if r2.type is RegisterType.is_to_save:
        string += save_register(r2)
    string += reset_register(e_register)
    e_register.type = RegisterType.is_unknown
    r1.is_blocked = False

    return r1, r2, string, a


# input: begin_for, commands,
# return [string]
def create_for_to(start_of_for_to, commands):
    for_variable = start_of_for_to[3]
    last_register_copy.pop()
    if isinstance(for_variable.value_from, Number) and isinstance(for_variable.value_to, Number):
        if for_variable.value_from.value > for_variable.value_to.value:
            load_registers()
            last_register_copy.pop()
            remove_for_variable_from_register(for_variable)
            return []
        else:
            if for_optimization:
                last_register_copy.pop()
                result = start_of_for_to[2] + commands
                b = [f"INC {start_of_for_to[0].name}"] + commands
                result += b * (for_variable.value_to.value - for_variable.value_from.value)
                remove_for_variable_from_register(for_variable)
                return result
    if len(commands) > 0:
        r1 = start_of_for_to[0]
        r2 = start_of_for_to[1]
        string = start_of_for_to[2]
        p1 = len(string)
        string += [
            f"ADD {e_register.name} {r1.name}",  # copy of r1
            f"SUB {e_register.name} {r2.name}",
            f"JZERO {e_register.name} 2",
            f"JUMP end",
        ]
        string += commands
        string += reset_register(e_register)
        string += load_variable_to_specific_register(for_variable.value_to, r2)
        r1.type = RegisterType.is_to_save
        # p2 = len(string)
        string += [
            f"INC {r1.name}"
        ]
        p3 = len(string)
        string.append("JUMP start")
        # replacing
        string[p1 + 3] = f"JUMP {len(string) - p1 - 3}"
        # string[p2] = f"JZERO {r1.name} {len(string) - p2}"
        string[p3] = f"JUMP {p1 - p3}"
        last_register_copy.pop()
        remove_for_variable_from_register(for_variable)
        e_register.type = RegisterType.is_unknown
        e_register.variable = None
        return string
    else:
        load_registers()
        last_register_copy.pop()
        remove_for_variable_from_register(for_variable)
        return []


def create_for_downto(start_of_for_to, commands):
    for_variable = start_of_for_to[3]
    last_register_copy.pop()
    if isinstance(for_variable.value_from, Number) and isinstance(for_variable.value_to, Number):
        if for_variable.value_from.value < for_variable.value_to.value:
            load_registers()
            last_register_copy.pop()
            remove_for_variable_from_register(for_variable)
            return []
        else:
            if for_optimization:
                last_register_copy.pop()
                result = start_of_for_to[2] + commands
                b = [f"DEC {start_of_for_to[0].name}"] + commands
                result += b * (for_variable.value_from.value - for_variable.value_to.value)
                remove_for_variable_from_register(for_variable)
                return result
    if len(commands) > 0:
        r1 = start_of_for_to[0]
        r2 = start_of_for_to[1]
        string = start_of_for_to[2]
        p1 = len(string)
        string += [
            f"ADD {e_register.name} {r2.name}",  # copy of r1
            f"SUB {e_register.name} {r1.name}",
            f"JZERO {e_register.name} 2",
            f"JUMP end",
        ]
        string += commands
        string += reset_register(e_register)
        string += load_variable_to_specific_register(for_variable.value_to, r2)
        r1.type = RegisterType.is_to_save
        p2 = len(string)
        string += [
            f"JZERO {r1.name} end",
            f"DEC {r1.name}"
        ]
        p3 = len(string)
        string.append("JUMP start")
        # replacing
        string[p1 + 3] = f"JUMP {len(string) - p1 - 3}"
        string[p2] = f"JZERO {r1.name} {len(string) - p2}"
        string[p3] = f"JUMP {p1 - p3}"
        last_register_copy.pop()
        e_register.type = RegisterType.is_unknown
        e_register.variable = None
        remove_for_variable_from_register(for_variable)

        return string
    else:
        load_registers()
        last_register_copy.pop()
        remove_for_variable_from_register(for_variable)
        return []


def remove_for_variable_from_register(variable):
    declared_variables.pop(variable.name)
    for register in registers.values():
        if are_variables_same(variable, register.variable) \
                or are_variables_same(variable.value_to, register.variable) \
                or isinstance(register.variable, TableValue) and are_variables_same(register.variable.move,
                                                                                    variable):
            register.variable = None
            register.type = RegisterType.is_unknown
    # print("Register restarted")


def variable_was_in_copy(variable):
    x = last_register_copy.pop()
    last_register_copy.append(x)
    for c in x[0] + x[1]:
        if are_variables_same(c.variable, variable):
            return True

    return False
