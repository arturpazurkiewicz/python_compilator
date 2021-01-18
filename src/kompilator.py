import argparse
import sys

from Logic import initialize_registers, generate_additional_numbers
from MyLexer import MyLexer
from MyParser import MyParser


def parse_arguments():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument(
        'input_file',
        help='.imp file'
    )
    argument_parser.add_argument(
        'output_file',
        help='.mr file'
    )
    return argument_parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    initialize_registers()
    with open(args.input_file, 'r') as input_file:
        code = input_file.read()
        lexer = MyLexer()
        parser = MyParser()
        commands = []
        try:
            parse_ready = lexer.tokenize(code)

            commands = parser.parse(parse_ready) + ["HALT"]
        except Exception as e:
            print(e)
            sys.exit(-1)

        commands = generate_additional_numbers() + commands
    with open(args.output_file, 'w') as output_file:
        output_file.write("\n".join(commands))
