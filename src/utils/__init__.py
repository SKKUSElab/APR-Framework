import ast
import re
import pylcs
from ordered_set import OrderedSet
from zss import Node, simple_distance

from .randoms import Randoms
from .ted import TED

def remove_comments_and_docstrings(code):
    # Remove single-line comments and strings that are used as comments
    code = re.sub(r'(?m)^\s*(#.*|\'[^\']*\'|"[^"]*")\s*$', '', code)
    # Remove multi-line comments and docstrings
    code = re.sub(r'(?s)(\'\'\'.*?\'\'\')|(""".*?""")', '', code)
    return code

def regular(code):
    return ast.unparse(ast.parse(code))

def regularize(code):
    code = regular(code)
    code = remove_comments_and_docstrings(code)
    return regular(code)


def get_stmt_list(code:str) -> list:
    return code.split('\n')

def get_indentation(stmt:str) -> int:
    return len(stmt.rstrip()) - len(stmt.strip())

def indent_replace(indent:int, stmt:str) -> str:
    return " " * indent + stmt.strip()

def longest_common_subsequence(list1, list2):
    unique_elements = sorted(OrderedSet(list1 + list2))
    char_list = [chr(i) for i in range(len(unique_elements))]
    if len(unique_elements) > len(char_list):
        raise Exception("too many elements")
    else:
        unique_element_map = {ele:char_list[i] for i, ele in enumerate(unique_elements)}
    list1_str = ''.join([unique_element_map[ele] for ele in list1])
    list2_str = ''.join([unique_element_map[ele] for ele in list2])

    lcs = pylcs.lcs_sequence_length(list1_str, list2_str)
    return lcs




def relative_patch_size(wrong, patch):
    patch_size = zss_code_distance(wrong, patch)
    bug_ast_size = zss_ast_size(wrong)
    return round(patch_size / bug_ast_size,2)


def str_node(node):
    if hasattr(node, "id"):
        return node.id
    elif hasattr(node, "name"):
        return node.name
    elif hasattr(node, "arg"):
        return node.arg
    elif hasattr(node, "n"):
        return str(node.n)
    elif hasattr(node, "s"):
        return "\'" + node.s + "\'"
    else:
        if node.__class__.__name__ in ["Module", "Load", "Store"]:
            return ""
        else:
            return node.__class__.__name__

def zss_ast_visit(ast_node, parent_zss_node):
    zss_label = str_node(ast_node)
    if zss_label == "":
        for field, value in ast.iter_fields(ast_node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        zss_ast_visit(item, parent_zss_node)
            elif isinstance(value, ast.AST):
                zss_ast_visit(value, parent_zss_node)
    else:
        zss_node = Node(zss_label)
        for field, value in ast.iter_fields(ast_node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        zss_ast_visit(item, zss_node)
            elif isinstance(value, ast.AST):
                zss_ast_visit(value, zss_node)
        parent_zss_node.addkid(zss_node)

def zss_node_cnt(zss_node):
    s = 1
    for child_zss_node in zss_node.children:
        s += zss_node_cnt(child_zss_node)
    return s

def zss_ast_size(code):
    root_node = ast.parse(code)
    root_zss_node = Node("root")
    zss_ast_visit(root_node, root_zss_node)
    return zss_node_cnt(root_zss_node)

def label_weight(l1, l2):
    if l1 == l2:
        return 0
    else:
        return 1


def zss_code_distance(code_a, code_b):
    root_node_a = ast.parse(code_a)
    root_zss_node_a = Node("root")
    zss_ast_visit(root_node_a, root_zss_node_a)

    root_node_b = ast.parse(code_b)
    root_zss_node_b = Node("root")
    zss_ast_visit(root_node_b, root_zss_node_b)

    return simple_distance(root_zss_node_a, root_zss_node_b, label_dist=label_weight)


def divide(a, b):
    try: res = a/b
    except ZeroDivisionError:
        res = 0
    return res