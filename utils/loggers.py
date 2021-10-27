import sys

def current_func_name(n=0):
    """
    0 - current function name
    1 - caller
    2 - caller of the caller
    """
    return sys._getframe(n + 1).f_code.co_name
