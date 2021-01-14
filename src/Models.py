import enum

from Logic import declared_variables


class Variable:
    def __init__(self, name, memory_address):
        self.assigned = False
        self.name = name
        self.memory_address = memory_address

    def __str__(self):
        return f"Variable: {self.name}, memory: {self.memory_address}"


class Number(Variable):
    def __init__(self, name, value, memory_address):
        self.value = value
        super().__init__(name, memory_address)
        self.assigned = True


class Table(Variable):
    def __init__(self, name, start, end, memory_address):
        self.start = int(start)
        self.end = int(end)
        if self.start > self.end:
            raise Exception("Invalid table " + name + " declaration")
        super().__init__(name, memory_address)


class TableValue(Variable):
    def __init__(self, name, move):
        if name not in declared_variables:
            raise Exception("Table " + name + " does not exist!!!")
        self.table = declared_variables[name]
        self.move = move
        memory_address = None
        if isinstance(move, Number):
            if not (self.table.start <= move.value <= self.table.end):
                raise Exception("A range outside the array value " + name)
            memory_address = move.value - self.table.start + self.table.memory_address
        super().__init__(name, memory_address)
        self.assigned = True


class Special(Variable):
    def __init__(self, name, memory_address):
        super(Special, self).__init__(name, memory_address)
        self.assigned = True


class RegisterType(enum.Enum):
    is_unknown = 'UNKNOWN'
    is_restarted = 'RESTARTED'
    is_variable = 'HAS VARIABLE'
    is_to_save = 'IS TO SAVE'


class Register:
    def __init__(self, name):
        self.name = name
        self.type = RegisterType.is_unknown
        self.is_blocked = False
        self.variable = None
        # move is used for Tables
        # self.move = None

    def __str__(self):
        return f"REGISTER: {self.name}, {self.variable}, type: {self.type}"


class LostRegister:
    def __init__(self, register, variable):
        self.register = register
        self.variable = variable,
