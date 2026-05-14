class SymbolTable:
    def __init__(self):
        self.scopes = [{}]

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def define(self, name, symbol_info):
        self.scopes[-1][name] = symbol_info

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def current_scope_contains(self, name):
        return name in self.scopes[-1]

    def is_global_scope(self):
        return len(self.scopes) == 1

class SemanticError(Exception):
    pass

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        self.in_function = False 

    def report_error(self, category, message, line):
        error_msg = f"[{category}] Error Semántico (Línea {line}): {message}"
        self.errors.append(error_msg)
        
    def analyze(self, node):
        self.visit(node)
        return self.errors

    def visit(self, node):
        if node is None:
            return None

        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        for attr, value in vars(node).items():
            if isinstance(value, list):
                for item in value:
                    self.visit(item)
            elif hasattr(value, "__dict__"):
                self.visit(value)

    def visit_ProgramNode(self, node):
        for stmt in node.statements:
            self.visit(stmt)