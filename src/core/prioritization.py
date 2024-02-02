import ast
from ..transform import DefUseChain
from ..utils import Randoms, relative_patch_size

class Prioritization:
    def __init__(self, programs:dict):
        self.programs = programs
    
    def _filtering(self, solutions:dict):
        # Filtering programs that has unbound variables
        for file, childs in solutions.items():
            valid_chillds = {}
            for p_id, child in childs.items():
                duc = DefUseChain()
                duc.run(child)
                if duc.unbound_vars:
                    continue
                valid_chillds[p_id] = child
            solutions[file] = valid_chillds
        return solutions
    
    def _deduplication(self, solutions:dict):
        # Deduplication programs that has same AST
        nomalize_dict = {}
        for file, childs in solutions.items():
            for p_id, child in childs.items():
                nomalize_code = self.__normalize(child)
                nomalize_dict.setdefault(nomalize_code, {}).setdefault(file, {})[p_id] = child
        for file, childs in nomalize_dict.values().items():
            if 1 < len(childs):
                p_id, child = Randoms.choice(list(childs.items()))
                solutions[file] = {p_id:child}
        return solutions
    
    def __normalize(self, code):
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                node.name = "class"
            if isinstance(node, ast.FunctionDef):
                node.name = "func"
            if isinstance(node, ast.Name):
                node.id = "name"
            if isinstance(node, ast.arg):
                node.arg = "arg"
        return ast.dump(tree)
    
    def run(self, solutions:dict) -> dict:
        feedbacks = {}
        # solutions = self._filtering(solutions)
        # solutions = self._deduplication(solutions)
        for file, childs in solutions.items():
            parent = self.programs[file]
            # First fit generation and patch
            first_gen, first_patch = min(list(childs.items()))
            # Minimum ted generation and patch
            min_gen, min_patch = min(childs.items(), key=lambda x: relative_patch_size(parent, x[1]))

            feedbacks[file] = (first_gen, first_patch, min_gen, min_patch)
        return feedbacks