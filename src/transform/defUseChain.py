import beniget, gast as ast

class DefUseChain(beniget.DefUseChains):
    def __init__(self, filename=None):
        super().__init__(filename)
        self.unbound_vars = set()

    def unbound_identifier(self, name, node):
        if hasattr(node, "lineno"):
            filename = "{}:".format(
                "<unknown>" if self.filename is None else self.filename
            )
            location = " at {}{}:{}".format(filename,
                                            node.lineno,
                                            node.col_offset)
        else:
            location = ""
        # print("W: unbound identifier '{}'{}".format(name, location))
        self.unbound_vars.add(name)
    
    def run(self, code):
        module = ast.parse(code)
        self.visit(module)


