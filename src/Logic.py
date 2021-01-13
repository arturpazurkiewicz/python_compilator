from src.Models import *

free_memory = 0

declared_variables = {}
registers = {}
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


def initialize_register():
    global registers
    registers["a"] = Register("a")
    registers["b"] = Register("b")
    registers["c"] = Register("c")
    registers["d"] = Register("d")
    registers["e"] = Register("e")