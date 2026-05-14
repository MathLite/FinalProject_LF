from ASTNode import *


def print_ast(node, indent=0):
    space = "    " * indent

    if node is None:
        print(space + "None")
        return

    # Programa
    if isinstance(node, ProgramNode):
        print(space + "ProgramNode")
        for stmt in node.statements:
            print_ast(stmt, indent + 1)

    # Bloque
    elif isinstance(node, BlockNode):
        print(space + "BlockNode")
        for stmt in node.statements:
            print_ast(stmt, indent + 1)

    # Literales y variables
    elif isinstance(node, NumberNode):
        print(space + "NumberNode: " + str(node.value))

    elif isinstance(node, StringNode):
        print(space + "StringNode: " + str(node.value))

    elif isinstance(node, BoolNode):
        print(space + "BoolNode: " + str(node.value))

    elif isinstance(node, VariableNode):
        print(space + "VariableNode: " + str(node.name))

    # Expresiones
    elif isinstance(node, BinOpNode):
        print(space + "BinOpNode: " + str(node.operator))
        print(space + "  left:")
        print_ast(node.left, indent + 2)
        print(space + "  right:")
        print_ast(node.right, indent + 2)

    elif isinstance(node, UnaryOpNode):
        print(space + "UnaryOpNode: " + str(node.operator))
        print(space + "  operand:")
        print_ast(node.operand, indent + 2)

    elif isinstance(node, FuncCallNode):
        print(space + "FuncCallNode: " + str(node.name))
        print(space + "  args:")
        for arg in node.args:
            print_ast(arg, indent + 2)

    # Sentencias
    elif isinstance(node, VarDeclNode):
        print(space + "VarDeclNode: " + str(node.name))
        print(space + "  value:")
        print_ast(node.value, indent + 2)

    elif isinstance(node, AssignNode):
        print(space + "AssignNode: " + str(node.name))
        print(space + "  value:")
        print_ast(node.value, indent + 2)

    elif isinstance(node, PrintNode):
        print(space + "PrintNode")
        print(space + "  expression:")
        print_ast(node.expression, indent + 2)

    elif isinstance(node, ReturnNode):
        print(space + "ReturnNode")
        print(space + "  expression:")
        print_ast(node.expression, indent + 2)

    elif isinstance(node, ExprStmtNode):
        print(space + "ExprStmtNode")
        print(space + "  expression:")
        print_ast(node.expression, indent + 2)

    elif isinstance(node, IfNode):
        print(space + "IfNode")
        print(space + "  condition:")
        print_ast(node.condition, indent + 2)
        print(space + "  then_block:")
        print_ast(node.then_block, indent + 2)
        print(space + "  else_block:")
        print_ast(node.else_block, indent + 2)

    elif isinstance(node, WhileNode):
        print(space + "WhileNode")
        print(space + "  condition:")
        print_ast(node.condition, indent + 2)
        print(space + "  body:")
        print_ast(node.body, indent + 2)

    elif isinstance(node, FuncDefNode):
        print(space + "FuncDefNode: " + str(node.name))
        print(space + "  params: " + str(node.params))
        print(space + "  body:")
        print_ast(node.body, indent + 2)

    else:
        print(space + "Nodo desconocido: " + str(type(node)))