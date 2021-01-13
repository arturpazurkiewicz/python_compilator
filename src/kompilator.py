import argparse
from MyLexer import MyLexer
from MyParser import MyParser
from Logic import declared_variables, initialize_register


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
    global declared_variables
    args = parse_arguments()
    with open(args.input_file, 'r') as input_file:
        code = input_file.read()
        lexer = MyLexer()
        parser = MyParser()
        # try:
        parse_ready = lexer.tokenize(code)
        parser.parse(parse_ready)
        # except Exception as e:
        #     print(e)
        commands = []

    with open(args.output_file, 'w') as output_file:
        output_file.write("\n".join(commands))
