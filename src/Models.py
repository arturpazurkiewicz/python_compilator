import enum


class Variable:
    def __init__(self, name, memory_address):
        self.name = name
        self.memory_address = memory_address


class Number(Variable):
    def __init__(self, name, value, memory_address):
        self.value = value
        super().__init__(name, memory_address)


class Table(Variable):
    def __init__(self, name, start, end, memory_address):
        self.start = start
        self.end = end
        super().__init__(name, memory_address)


class Special(Variable):
    def __init__(self, name, memory_address):
        super(Special, self).__init__(name, memory_address)


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
        # move is used for Tables
        self.move = None


class LostRegister:
    def __init__(self, register_name, variable, move):
        self.register_name = register_name,
        self.variable = variable,
        self.move = move