#-----------------------------------------------------------------
# pycparser: __init__.py
#
# This package file exports some convenience functions for
# interacting with pycparser
#
# Eli Bendersky [http://eli.thegreenplace.net]
# License: BSD
#-----------------------------------------------------------------
__all__ = ['c_lexer', 'c_parser', 'c_ast']
__version__ = '2.17'

from subprocess import Popen, PIPE
from .c_parser import CParser
from .ply import cpp
from .ply import lex


def preprocess_file_embedded(filename, cpp_path=None, cpp_args=''):
    if not isinstance(cpp_args, list):
        cpp_args = [cpp_args]

    lexer = lex.lex(module=cpp)
    try:
        if issubclass(cpp_path, cpp.Preprocessor):
            preprocessor = cpp_path
        else:
            raise TypeError
    except TypeError:
        preprocessor = cpp.Preprocessor
    p = preprocessor(lexer)

    for cpp_arg in cpp_args:
        if cpp_arg[:2] == '-I':
            p.add_path(cpp_arg[2:])
        elif cpp_arg[:2] == '-D':
            p.define(cpp_args[2:].replace('=', ' ', 1))

    with open(filename, 'rU') as f:
        p.parse(f.read(), filename)

    processed = []
    latest = ''
    while True:
        tok = p.token()
        if not tok:
            break

        if latest != p.source:
            processed.append('\n# {} "{}"\n'.format(tok.lineno, p.source))
            latest = p.source

        processed.append(tok.value)

    return ''.join(processed)


def preprocess_file(filename, cpp_path='cpp', cpp_args=''):
    """ Preprocess a file using cpp.

        filename:
            Name of the file you want to preprocess.

        cpp_path:
        cpp_args:
            Refer to the documentation of parse_file for the meaning of these
            arguments.

        When successful, returns the preprocessed file's contents.
        Errors from cpp will be printed out.
    """
    path_list = [cpp_path]
    if isinstance(cpp_args, list):
        path_list += cpp_args
    elif cpp_args != '':
        path_list += [cpp_args]
    path_list += [filename]

    try:
        # Note the use of universal_newlines to treat all newlines
        # as \n for Python's purpose
        #
        pipe = Popen(   path_list,
                        stdout=PIPE,
                        universal_newlines=True)
        text = pipe.communicate()[0]
    except OSError as e:
        raise RuntimeError("Unable to invoke 'cpp'.  " +
            'Make sure its path was passed correctly\n' +
            ('Original error: %s' % e))

    return text


def parse_file(filename, use_cpp=False, cpp_path='cpp', cpp_args='',
               parser=None):
    """ Parse a C file using pycparser.

        filename:
            Name of the file you want to parse.

        use_cpp:
            Set to True if you want to execute the C pre-processor
            on the file prior to parsing it.

        cpp_path:
            If use_cpp is True, this is the path to 'cpp' on your
            system. If no path is provided, it attempts to just
            execute 'cpp', so it must be in your PATH.

        cpp_args:
            If use_cpp is True, set this to the command line arguments strings
            to cpp. Be careful with quotes - it's best to pass a raw string
            (r'') here. For example:
            r'-I../utils/fake_libc_include'
            If several arguments are required, pass a list of strings.

        parser:
            Optional parser object to be used instead of the default CParser

        When successful, an AST is returned. ParseError can be
        thrown if the file doesn't parse successfully.

        Errors from cpp will be printed out.
    """
    if use_cpp == "embedded":
        text = preprocess_file_embedded(filename, cpp_path, cpp_args)
    elif use_cpp:
        text = preprocess_file(filename, cpp_path, cpp_args)
    else:
        with open(filename, 'rU') as f:
            text = f.read()

    if parser is None:
        parser = CParser()
    return parser.parse(text, filename)
