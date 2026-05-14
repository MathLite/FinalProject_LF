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

    def visit_VarDeclNode(self, node):
        value_type = self.visit(node.value)

        if self.symbol_table.current_scope_contains(node.name):
            self.report_error(
                "REDECLARED_VAR", 
                f"La variable '{node.name}' ya fue declarada en este bloque.", 
                node.line
            )
        else:
            self.symbol_table.define(node.name, {"type": value_type, "kind": "VAR"})
        
        node.eval_type = value_type
        return value_type
    
    def visit_VariableNode(self, node):
        symbol = self.symbol_table.lookup(node.name)

        if symbol is None:
            self.report_error(
                "UNDECLARED_VAR", 
                f"La variable '{node.name}' no ha sido declarada antes de su uso.", 
                node.line
            )
            node.eval_type = "ERROR"
            return "ERROR"

        node.eval_type = symbol["type"]
        return node.eval_type

    def visit_AssignNode(self, node):
        value_type = self.visit(node.value)
        symbol = self.symbol_table.lookup(node.name)

        if symbol is None:
            self.report_error(
                "UNDECLARED_VAR", 
                f"No se puede asignar un valor a '{node.name}' porque no ha sido declarada.", 
                node.line
            )
            node.eval_type = "ERROR"
            return "ERROR"

        node.eval_type = value_type
        return value_type

    def visit_FuncDefNode(self, node):
        if self.symbol_table.current_scope_contains(node.name):
            self.report_error(
                "REDECLARED_FUNC", 
                f"El nombre '{node.name}' ya fue declarado en este alcance. No puedes redeclarar esta función.", 
                node.line
            )
        else:
            self.symbol_table.define(node.name, {
                "type": "FUNC", 
                "arity": len(node.params)
            })

        self.symbol_table.enter_scope() 
        self.in_function = True         

        for param_name in node.params:
            if self.symbol_table.current_scope_contains(param_name):
                self.report_error(
                    "REDECLARED_VAR", 
                    f"El parámetro '{param_name}' está duplicado en la definición de la función '{node.name}'.", 
                    node.line
                )
            else:
                self.symbol_table.define(param_name, {"type": "ANY", "kind": "PARAM"})
        
        if node.body:
            self.visit(node.body)

        self.in_function = False       
        self.symbol_table.exit_scope() 
    
    def visit_FuncCallNode(self, node):
        func_symbol = self.symbol_table.lookup(node.name)

        if func_symbol is None or func_symbol.get("type") != "FUNC":
            self.report_error(
                "UNDECLARED_FUNC", 
                f"La función '{node.name}' no está definida antes de ser llamada.", 
                node.line
            )
            node.eval_type = "ERROR"
            return "ERROR"

        expected_arity = func_symbol.get("arity", 0)
        actual_arity = len(node.args)

        if expected_arity != actual_arity:
            self.report_error(
                "ARITY_MISMATCH", 
                f"La función '{node.name}' espera {expected_arity} argumentos, pero recibió {actual_arity}.", 
                node.line
            )

        for arg in node.args:
            self.visit(arg)

        node.eval_type = "ANY"
        return "ANY"

    # ==========================================
    # LITERALES 
    # ==========================================
    def visit_NumberNode(self, node):
        if '.' in str(node.value):
            node.eval_type = "REAL"
        else:
            node.eval_type = "INT"
        return node.eval_type

    def visit_StringNode(self, node):
        node.eval_type = "STRING"
        return "STRING"

    def visit_BoolNode(self, node):
        node.eval_type = "BOOL"
        return "BOOL"

    # ==========================================
    # OPERACIONES BINARIAS
    # ==========================================
    def visit_BinOpNode(self, node):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        if left_type == "ERROR" or right_type == "ERROR":
            node.eval_type = "ERROR"
            return "ERROR"

        arithmetic_ops = ["+", "-", "*", "/", "%", "^"]
        relational_ops = [">", "<", ">=", "<=", "==", "!="]
        logical_ops = ["and", "or"]

        if node.operator in arithmetic_ops:
            if left_type in ["STRING", "BOOL"] or right_type in ["STRING", "BOOL"]:
                self.report_error(
                    "TYPE_MISMATCH", 
                    f"Operación aritmética '{node.operator}' inválida entre tipos {left_type} y {right_type}.", 
                    node.line
                )
                node.eval_type = "ERROR"
                return "ERROR"

            if left_type == "REAL" or right_type == "REAL":
                node.eval_type = "REAL"
            else:
                node.eval_type = "INT"
                
            return node.eval_type

        elif node.operator in relational_ops:
            node.eval_type = "BOOL"
            return "BOOL"

        elif node.operator in logical_ops:
            node.eval_type = "BOOL"
            return "BOOL"

        node.eval_type = "ANY"
        return "ANY"