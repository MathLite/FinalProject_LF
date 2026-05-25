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
        print(space + f"NumberNode: {node.value} (L:{node.line})")  

    elif isinstance(node, StringNode):
        print(space + f"StringNode: {node.value} (L:{node.line})")

    elif isinstance(node, BoolNode):
        print(space + f"BoolNode: {node.value} (L:{node.line})")  

    elif isinstance(node, VariableNode):
        print(space + f"VariableNode: {node.name} (L:{node.line})")

    # Expresiones
    elif isinstance(node, BinOpNode):
        print(space + f"BinOpNode: {node.operator} (L:{node.line})")
        print(space + "  left:")
        print_ast(node.left, indent + 2)
        print(space + "  right:")
        print_ast(node.right, indent + 2)

    elif isinstance(node, UnaryOpNode):
        print(space + f"UnaryOpNode: {node.operator} (L:{node.line})")
        print(space + "  operand:")
        print_ast(node.operand, indent + 2)

    elif isinstance(node, FuncCallNode):
        print(space + f"FuncCallNode: {node.name} (L:{node.line})")
        print(space + "  args:")
        for arg in node.args:
            print_ast(arg, indent + 2)

    # Sentencias
    elif isinstance(node, VarDeclNode):
        print(space + f"VarDeclNode: {node.name} (L:{node.line})")
        print(space + "  value:")
        print_ast(node.value, indent + 2)

    elif isinstance(node, PrintNode):
        print(space + f"PrintNode (L:{node.line})")
        print(space + "  expression:")
        print_ast(node.expression, indent + 2)

    elif isinstance(node, ReturnNode):
        print(space + f"ReturnNode (L:{node.line})")
        print(space + "  expression:")
        print_ast(node.expression, indent + 2)

    elif isinstance(node, ExprStmtNode):
        print(space + f"ExprStmtNode (L:{node.line})")
        print(space + "  expression:")
        print_ast(node.expression, indent + 2)

    elif isinstance(node, IfNode):
        print(space + f"IfNode (L:{node.line})")
        print(space + "  condition:")
        print_ast(node.condition, indent + 2)
        print(space + "  then_block:")
        print_ast(node.then_block, indent + 2)
        print(space + "  else_block:")
        print_ast(node.else_block, indent + 2)

    elif isinstance(node, WhileNode):
        print(space + f"WhileNode (L:{node.line})")
        print(space + "  condition:")
        print_ast(node.condition, indent + 2)
        print(space + "  body:")
        print_ast(node.body, indent + 2)

    elif isinstance(node, FuncDefNode):
        print(space + f"FuncDefNode: {node.name} (L:{node.line})")
        print(space + "  params: " + str(node.params))
        print(space + "  body:")
        print_ast(node.body, indent + 2)

    else:
        print(space + "Nodo desconocido: " + str(type(node)))