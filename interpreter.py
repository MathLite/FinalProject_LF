import math
from ASTNode import *


class RuntimeErrorInfo:
    def __init__(self, message, line=0):
        self.message = message
        self.line = line

    def __str__(self):
        if self.line:
            return "Error en tiempo de ejecución (Línea {}): {}".format(
                self.line,
                self.message
            )

        return "Error en tiempo de ejecución: {}".format(self.message)


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class MathLiteRuntimeError(Exception):
    def __init__(self, node, message):
        super().__init__(message)
        self.node = node
        self.message = message


class Environment:
    def __init__(self, parent=None, is_function_scope=False):
        self.values = {}
        self.parent = parent
        self.is_function_scope = is_function_scope

    def define(self, name, value):
        self.values[name] = value

    def find_for_assignment(self, name):
        env = self

        while env is not None:
            if name in env.values:
                return env

            if env.is_function_scope:
                break

            env = env.parent

        return None

    def define_or_assign(self, name, value):
        target_env = self.find_for_assignment(name)

        if target_env is not None:
            target_env.values[name] = value
        else:
            self.define(name, value)

    def assign(self, name, value):
        target_env = self.find_for_assignment(name)

        if target_env is not None:
            target_env.values[name] = value
            return

        raise RuntimeError("La variable '{}' no está definida.".format(name))

    def get(self, name):
        if name in self.values:
            return self.values[name]

        if self.parent is not None:
            return self.parent.get(name)

        raise RuntimeError("La variable '{}' no está definida.".format(name))
    
class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.current_env = self.global_env
        self.functions = {}
        self.output = []
        self.errors = []
        self.max_loop_iterations = 10000

        self.builtin_functions = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "sqrt": math.sqrt,
            "log": math.log,
            "abs": abs,
            "floor": math.floor,
            "ceil": math.ceil,
        }

    def reset_runtime_state(self):
        self.global_env = Environment()
        self.current_env = self.global_env
        self.functions = {}
        self.output = []
        self.errors = []

    def interpret(self, ast):
        self.reset_runtime_state()

        try:
            self.visit(ast)
        except ReturnSignal:
            self.errors.append(
                RuntimeErrorInfo("La instrucción return no puede ejecutarse fuera de una función.")
            )
        except MathLiteRuntimeError as error:
            self.errors.append(RuntimeErrorInfo(error.message, line=error.node.line if error.node else 0))
        except Exception as error:
            self.errors.append(RuntimeErrorInfo(str(error)))

        return self.output, self.errors

    def visit(self, node):
        if node is None:
            return None

        method_name = "visit_" + type(node).__name__
        method = getattr(self, method_name, None)

        if method is None:
            raise MathLiteRuntimeError(
                node,
                "No existe método de interpretación para el nodo '{}'.".format(
                    type(node).__name__
                )
            )

        return method(node)

    # =========================
    # PROGRAMA Y BLOQUES
    # =========================

    def visit_ProgramNode(self, node):
        for statement in node.statements:
            self.visit(statement)

    def visit_BlockNode(self, node):
        for statement in node.statements:
            self.visit(statement)

    # =========================
    # SENTENCIAS
    # =========================

    def visit_VarDeclNode(self, node):
        value = self.visit(node.value)
        self.current_env.define_or_assign(node.name, value)
        return value

    def visit_AssignNode(self, node):
        value = self.visit(node.value)
        self.current_env.assign(node.name, value)
        return value

    def visit_PrintNode(self, node):
        value = self.visit(node.expression)
        self.output.append(self.format_value(value))
        return value

    def visit_ReturnNode(self, node):
        value = self.visit(node.expression)
        raise ReturnSignal(value)

    def visit_ExprStmtNode(self, node):
        return self.visit(node.expression)

    def visit_IfNode(self, node):
        condition = self.visit(node.condition)

        if self.is_truthy(condition):
            for statement in node.then_block.statements:
                self.visit(statement)
            return None

        if node.else_block is not None:
            for statement in node.else_block.statements:
                self.visit(statement)

        return None
    
    def visit_WhileNode(self, node):
        iterations = 0

        while self.is_truthy(self.visit(node.condition)):
            if iterations >= self.max_loop_iterations:
                raise RuntimeError("Se superó el límite de iteraciones. Posible ciclo infinito.")

            for statement in node.body.statements:
                self.visit(statement)

            iterations += 1

        return None
    
    def visit_FuncDefNode(self, node):
        self.functions[node.name] = node
        return None

    # =========================
    # LITERALES Y VARIABLES
    # =========================

    def visit_NumberNode(self, node):
        if "." in str(node.value):
            return float(node.value)

        return int(node.value)

    def visit_StringNode(self, node):
        value = node.value

        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            return value[1:-1]

        return value

    def visit_BoolNode(self, node):
        return node.value

    def visit_VariableNode(self, node):
        try:
            return self.current_env.get(node.name)
        except RuntimeError as error:
            raise MathLiteRuntimeError(node, str(error))

    # =========================
    # EXPRESIONES
    # =========================

    def visit_UnaryOpNode(self, node):
        value = self.visit(node.operand)

        if node.operator == "-":
            self.validate_number(node, value, "El operador '-' requiere un valor numérico.")
            return -value

        if node.operator == "not":
            return not self.is_truthy(value)

        raise MathLiteRuntimeError(node, "Operador unario no soportado '{}'.".format(node.operator))

    def visit_BinOpNode(self, node):
        if node.operator == "and":
            left = self.visit(node.left)

            if not self.is_truthy(left):
                return False

            right = self.visit(node.right)
            return self.is_truthy(right)

        if node.operator == "or":
            left = self.visit(node.left)

            if self.is_truthy(left):
                return True

            right = self.visit(node.right)
            return self.is_truthy(right)

        left = self.visit(node.left)
        right = self.visit(node.right)

        if node.operator == "+":
            return self.evaluate_plus(node, left, right)

        if node.operator == "-":
            self.validate_numbers(node, left, right, "El operador '-' requiere valores numéricos.")
            return left - right

        if node.operator == "*":
            self.validate_numbers(node, left, right, "El operador '*' requiere valores numéricos.")
            return left * right

        if node.operator == "/":
            self.validate_numbers(node, left, right, "El operador '/' requiere valores numéricos.")

            if right == 0:
                raise MathLiteRuntimeError(node, "División por cero.")

            return left / right

        if node.operator == "%":
            self.validate_numbers(node, left, right, "El operador '%' requiere valores numéricos.")

            if right == 0:
                raise MathLiteRuntimeError(node, "Módulo por cero.")

            return left % right

        if node.operator == "^":
            self.validate_numbers(node, left, right, "El operador '^' requiere valores numéricos.")
            return left ** right

        if node.operator == "==":
            return left == right

        if node.operator == "!=":
            return left != right

        if node.operator == "<":
            self.validate_numbers(node, left, right, "El operador '<' requiere valores numéricos.")
            return left < right

        if node.operator == ">":
            self.validate_numbers(node, left, right, "El operador '>' requiere valores numéricos.")
            return left > right

        if node.operator == "<=":
            self.validate_numbers(node, left, right, "El operador '<=' requiere valores numéricos.")
            return left <= right

        if node.operator == ">=":
            self.validate_numbers(node, left, right, "El operador '>=' requiere valores numéricos.")
            return left >= right

        raise MathLiteRuntimeError(node, "Operador binario no soportado '{}'.".format(node.operator))

    def visit_FuncCallNode(self, node):
        arguments = []

        for arg in node.args:
            arguments.append(self.visit(arg))

        if node.name in self.builtin_functions:
            return self.call_builtin_function(node, node.name, arguments)

        if node.name not in self.functions:
            raise MathLiteRuntimeError(node, "Función '{}' no encontrada.".format(node.name))

        function_node = self.functions[node.name]

        if len(arguments) != len(function_node.params):
            raise MathLiteRuntimeError(
                node,
                "La función '{}' esperaba {} argumentos, pero recibió {}.".format(
                    node.name,
                    len(function_node.params),
                    len(arguments)
                )
            )

        previous_env = self.current_env
        local_env = Environment(parent=self.global_env, is_function_scope=True)
       
        for index in range(len(function_node.params)):
            param_name = function_node.params[index]
            local_env.define(param_name, arguments[index])

        self.current_env = local_env

        try:
            self.visit(function_node.body)
        except ReturnSignal as return_signal:
            self.current_env = previous_env
            return return_signal.value
        finally:
            self.current_env = previous_env

        return None

    # =========================
    # FUNCIONES INTEGRADAS
    # =========================

    def call_builtin_function(self, node, name, arguments):
        if len(arguments) != 1:
            raise MathLiteRuntimeError(
                node,
                "La función integrada '{}' espera 1 argumento.".format(name)
            )

        value = arguments[0]

        if not self.is_number(value):
            raise MathLiteRuntimeError(
                node,
                "La función integrada '{}' requiere un argumento numérico.".format(name)
            )

        try:
            return self.builtin_functions[name](value)
        except ValueError:
            raise MathLiteRuntimeError(
                node,
                "Argumento inválido para la función integrada '{}'.".format(name)
            )

    # =========================
    # UTILIDADES
    # =========================

    def is_number(self, value):
        return isinstance(value, int) or isinstance(value, float)

    def validate_number(self, node, value, message):
        if not self.is_number(value):
            raise MathLiteRuntimeError(node, message)

    def validate_numbers(self, node, left, right, message):
        if not self.is_number(left) or not self.is_number(right):
            raise MathLiteRuntimeError(node, message)

    def evaluate_plus(self, node, left, right):
        if self.is_number(left) and self.is_number(right):
            return left + right

        if isinstance(left, str) and isinstance(right, str):
            return left + right

        raise MathLiteRuntimeError(node, "El operador '+' solo permite número + número o cadena + cadena.")

    def is_truthy(self, value):
        if value is None:
            return False

        if isinstance(value, bool):
            return value

        if self.is_number(value):
            return value != 0

        if isinstance(value, str):
            return len(value) > 0

        return True

    def format_value(self, value):
        if isinstance(value, bool):
            if value:
                return "true"
            return "false"

        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))

            return str(value)

        return str(value)