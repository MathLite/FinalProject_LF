class SymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.scope_types = ["global"]

    def enter_scope(self, scope_type="block"):
        self.scopes.append({})
        self.scope_types.append(scope_type)

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
            self.scope_types.pop()

    def define(self, name, symbol_info):
        self.scopes[-1][name] = symbol_info

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        return None

    def lookup_for_assignment(self, name):
        for index in range(len(self.scopes) - 1, -1, -1):
            scope = self.scopes[index]

            if name in scope:
                return scope[name]

            if self.scope_types[index] == "function":
                break

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

        self.builtin_functions = {
            "sin": {"arity": 1, "return_type": "REAL"},
            "cos": {"arity": 1, "return_type": "REAL"},
            "tan": {"arity": 1, "return_type": "REAL"},
            "sqrt": {"arity": 1, "return_type": "REAL"},
            "log": {"arity": 1, "return_type": "REAL"},
            "abs": {"arity": 1, "return_type": "ANY"},
            "floor": {"arity": 1, "return_type": "INT"},
            "ceil": {"arity": 1, "return_type": "INT"},
        }

        self.register_builtin_functions()

    def register_builtin_functions(self):
        for name, info in self.builtin_functions.items():
            self.symbol_table.define(name, {
                "type": "FUNC",
                "kind": "BUILTIN_FUNC",
                "arity": info["arity"],
                "return_type": info["return_type"]
            })

    def report_error(self, category, message, line):
        error_msg = "[{}] Error Semántico (Línea {}): {}".format(
            category,
            line,
            message
        )
        self.errors.append(error_msg)

    def analyze(self, node):
        self.errors = []
        self.visit(node)
        return self.errors

    def visit(self, node):
        if node is None:
            return None

        method_name = "visit_" + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)

        return visitor(node)

    def generic_visit(self, node):
        for attr, value in vars(node).items():
            if isinstance(value, list):
                for item in value:
                    self.visit(item)
            elif hasattr(value, "__dict__"):
                self.visit(value)

    # =========================
    # PROGRAMA Y BLOQUES
    # =========================

    def visit_ProgramNode(self, node):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_BlockNode(self, node):
        for stmt in node.statements:
            self.visit(stmt)

    # =========================
    # DECLARACIONES
    # =========================

    def visit_VarDeclNode(self, node):
        value_type = self.visit(node.value)

        target_symbol = self.symbol_table.lookup_for_assignment(node.name)

        if target_symbol is not None:
            if target_symbol.get("type") == "FUNC":
                self.report_error(
                    "INVALID_REDECLARATION",
                    "El nombre '{}' corresponde a una función y no puede usarse como variable.".format(node.name),
                    node.line
                )
                node.eval_type = "ERROR"
                return "ERROR"

            target_symbol["type"] = value_type
            node.eval_type = value_type
            return value_type

        self.symbol_table.define(node.name, {
            "type": value_type,
            "kind": "VAR"
        })

        node.eval_type = value_type
        return value_type

    def visit_FuncDefNode(self, node):
        if self.symbol_table.current_scope_contains(node.name):
            self.report_error(
                "REDECLARED_FUNC",
                "El nombre '{}' ya fue declarado en este alcance. No puedes redeclarar esta función.".format(node.name),
                node.line
            )
        else:
            self.symbol_table.define(node.name, {
                "type": "FUNC",
                "kind": "USER_FUNC",
                "arity": len(node.params),
                "return_type": "ANY"
            })

        previous_in_function = self.in_function
        self.in_function = True

        self.symbol_table.enter_scope("function")

        for param_name in node.params:
            if self.symbol_table.current_scope_contains(param_name):
                self.report_error(
                    "REDECLARED_VAR",
                    "El parámetro '{}' está duplicado en la definición de la función '{}'.".format(
                        param_name,
                        node.name
                    ),
                    node.line
                )
            else:
                self.symbol_table.define(param_name, {
                    "type": "ANY",
                    "kind": "PARAM"
                })

        if node.body:
            self.visit(node.body)

        self.symbol_table.exit_scope()
        self.in_function = previous_in_function

        node.eval_type = "FUNC"
        return "FUNC"

    # =========================
    # SENTENCIAS
    # =========================

    def visit_PrintNode(self, node):
        expr_type = self.visit(node.expression)
        node.eval_type = expr_type
        return expr_type

    def visit_ReturnNode(self, node):
        if not self.in_function:
            self.report_error(
                "INVALID_RETURN",
                "La instrucción 'return' es inválida en este contexto. Solo puede usarse dentro del cuerpo de una función.",
                node.line
            )

        expr_type = self.visit(node.expression)
        node.eval_type = expr_type
        return expr_type

    def visit_ExprStmtNode(self, node):
        expr_type = self.visit(node.expression)
        node.eval_type = expr_type
        return expr_type

    def visit_IfNode(self, node):
        condition_type = self.visit(node.condition)

        if condition_type not in ["BOOL", "ERROR"]:
            self.report_error(
                "INVALID_CONDITION",
                "La condición del if debe ser de tipo BOOL.",
                node.line
            )

        self.visit(node.then_block)

        if node.else_block is not None:
            self.visit(node.else_block)

        node.eval_type = "VOID"
        return "VOID"

    def visit_WhileNode(self, node):
        condition_type = self.visit(node.condition)

        if condition_type not in ["BOOL", "ERROR"]:
            self.report_error(
                "INVALID_CONDITION",
                "La condición del while debe ser de tipo BOOL.",
                node.line
            )

        self.visit(node.body)

        node.eval_type = "VOID"
        return "VOID"

    # =========================
    # VARIABLES Y FUNCIONES
    # =========================

    def visit_VariableNode(self, node):
        symbol = self.symbol_table.lookup(node.name)

        if symbol is None:
            self.report_error(
                "UNDECLARED_VAR",
                "La variable '{}' no ha sido declarada antes de su uso.".format(node.name),
                node.line
            )
            node.eval_type = "ERROR"
            return "ERROR"

        if symbol.get("type") == "FUNC":
            self.report_error(
                "INVALID_VAR_USAGE",
                "El nombre '{}' corresponde a una función y no puede usarse como variable.".format(node.name),
                node.line
            )
            node.eval_type = "ERROR"
            return "ERROR"

        node.eval_type = symbol["type"]
        return node.eval_type

    def visit_FuncCallNode(self, node):
        func_symbol = self.symbol_table.lookup(node.name)

        if func_symbol is None or func_symbol.get("type") != "FUNC":
            self.report_error(
                "UNDECLARED_FUNC",
                "La función '{}' no está definida antes de ser llamada.".format(node.name),
                node.line
            )
            node.eval_type = "ERROR"
            return "ERROR"

        expected_arity = func_symbol.get("arity", 0)
        actual_arity = len(node.args)

        if expected_arity != actual_arity:
            self.report_error(
                "ARITY_MISMATCH",
                "La función '{}' espera {} argumentos, pero recibió {}.".format(
                    node.name,
                    expected_arity,
                    actual_arity
                ),
                node.line
            )

        arg_types = []

        for arg in node.args:
            arg_type = self.visit(arg)
            arg_types.append(arg_type)

        if func_symbol.get("kind") == "BUILTIN_FUNC":
            for arg_type in arg_types:
                if arg_type not in ["INT", "REAL", "ERROR"]:
                    self.report_error(
                        "TYPE_MISMATCH",
                        "La función integrada '{}' requiere argumentos numéricos.".format(node.name),
                        node.line
                    )
                    node.eval_type = "ERROR"
                    return "ERROR"

            return_type = func_symbol.get("return_type", "ANY")

            if return_type == "ANY":
                if len(arg_types) > 0:
                    node.eval_type = arg_types[0]
                else:
                    node.eval_type = "ANY"
            else:
                node.eval_type = return_type

            return node.eval_type

        node.eval_type = func_symbol.get("return_type", "ANY")
        return node.eval_type

    # =========================
    # LITERALES
    # =========================

    def visit_NumberNode(self, node):
        if "." in str(node.value):
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

    # =========================
    # OPERACIONES
    # =========================
    def is_numeric_type(self, value_type):
        return value_type in ["INT", "REAL"]


    def is_numeric_or_any(self, value_type):
        return value_type in ["INT", "REAL", "ANY"]


    def is_bool_or_any(self, value_type):
        return value_type in ["BOOL", "ANY"]

    def visit_BinOpNode(self, node):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        if left_type == "ERROR" or right_type == "ERROR":
            node.eval_type = "ERROR"
            return "ERROR"

        arithmetic_ops = ["+", "-", "*", "/", "%", "^"]
        relational_numeric_ops = [">", "<", ">=", "<="]
        equality_ops = ["==", "!="]
        logical_ops = ["and", "or"]

        if node.operator in arithmetic_ops:
            if not self.is_numeric_or_any(left_type) or not self.is_numeric_or_any(right_type):
                self.report_error(
                    "TYPE_MISMATCH",
                    "Operación aritmética '{}' inválida entre tipos {} y {}.".format(
                        node.operator,
                        left_type,
                        right_type
                    ),
                    node.line
                )
                node.eval_type = "ERROR"
                return "ERROR"

            if left_type == "ANY" or right_type == "ANY":
                node.eval_type = "ANY"
                return "ANY"

            if left_type == "REAL" or right_type == "REAL":
                node.eval_type = "REAL"
            else:
                node.eval_type = "INT"

            return node.eval_type

        if node.operator in relational_numeric_ops:
            if not self.is_numeric_or_any(left_type) or not self.is_numeric_or_any(right_type):
                self.report_error(
                    "TYPE_MISMATCH",
                    "El operador '{}' requiere operandos numéricos.".format(node.operator),
                    node.line
                )
                node.eval_type = "ERROR"
                return "ERROR"

            node.eval_type = "BOOL"
            return "BOOL"

        if node.operator in equality_ops:
            node.eval_type = "BOOL"
            return "BOOL"

        if node.operator in logical_ops:
            if not self.is_bool_or_any(left_type) or not self.is_bool_or_any(right_type):
                self.report_error(
                    "TYPE_MISMATCH",
                    "El operador lógico '{}' requiere operandos booleanos.".format(node.operator),
                    node.line
                )
                node.eval_type = "ERROR"
                return "ERROR"

            node.eval_type = "BOOL"
            return "BOOL"

        node.eval_type = "ANY"
        return "ANY"

    def visit_UnaryOpNode(self, node):
        operand_type = self.visit(node.operand)

        if operand_type == "ERROR":
            node.eval_type = "ERROR"
            return "ERROR"

        if node.operator == "-":
            if operand_type not in ["INT", "REAL"]:
                self.report_error(
                    "TYPE_MISMATCH",
                    "El operador '-' requiere un valor numérico.",
                    node.line
                )
                node.eval_type = "ERROR"
                return "ERROR"

            node.eval_type = operand_type
            return operand_type

        if node.operator == "not":
            if operand_type != "BOOL":
                self.report_error(
                    "TYPE_MISMATCH",
                    "El operador 'not' requiere un valor booleano.",
                    node.line
                )
                node.eval_type = "ERROR"
                return "ERROR"

            node.eval_type = "BOOL"
            return "BOOL"

        node.eval_type = "ERROR"
        return "ERROR"