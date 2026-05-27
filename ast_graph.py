from ASTNode import *


class ASTGraphBuilder:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.counter = 0

    def next_id(self):
        self.counter += 1
        return self.counter

    def add_node(self, label):
        node_id = self.next_id()
        self.nodes.append({
            "id": node_id,
            "label": label
        })
        return node_id

    def add_edge(self, parent_id, child_id):
        self.edges.append({
            "from": parent_id,
            "to": child_id
        })

    def build(self, ast):
        self.visit(ast)
        return {
            "nodes": self.nodes,
            "edges": self.edges
        }

    def visit(self, node):
        if node is None:
            return self.add_node("None")

        method_name = "visit_" + node.__class__.__name__
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        return self.add_node(node.__class__.__name__)

    def visit_ProgramNode(self, node):
        node_id = self.add_node("ProgramNode")

        for stmt in node.statements:
            child_id = self.visit(stmt)
            self.add_edge(node_id, child_id)

        return node_id

    def visit_BlockNode(self, node):
        node_id = self.add_node("BlockNode")

        for stmt in node.statements:
            child_id = self.visit(stmt)
            self.add_edge(node_id, child_id)

        return node_id

    def visit_NumberNode(self, node):
        return self.add_node("NumberNode\\n{}".format(node.value))

    def visit_StringNode(self, node):
        return self.add_node("StringNode\\n{}".format(node.value))

    def visit_BoolNode(self, node):
        return self.add_node("BoolNode\\n{}".format(node.value))

    def visit_VariableNode(self, node):
        return self.add_node("VariableNode\\n{}".format(node.name))

    def visit_BinOpNode(self, node):
        node_id = self.add_node("BinOpNode\\n{}".format(node.operator))

        left_id = self.visit(node.left)
        right_id = self.visit(node.right)

        self.add_edge(node_id, left_id)
        self.add_edge(node_id, right_id)

        return node_id

    def visit_UnaryOpNode(self, node):
        node_id = self.add_node("UnaryOpNode\\n{}".format(node.operator))

        operand_id = self.visit(node.operand)
        self.add_edge(node_id, operand_id)

        return node_id

    def visit_FuncCallNode(self, node):
        node_id = self.add_node("FuncCallNode\\n{}".format(node.name))

        for arg in node.args:
            child_id = self.visit(arg)
            self.add_edge(node_id, child_id)

        return node_id

    def visit_VarDeclNode(self, node):
        node_id = self.add_node("VarDeclNode\\n{}".format(node.name))

        value_id = self.visit(node.value)
        self.add_edge(node_id, value_id)

        return node_id

    def visit_PrintNode(self, node):
        node_id = self.add_node("PrintNode")

        expr_id = self.visit(node.expression)
        self.add_edge(node_id, expr_id)

        return node_id

    def visit_ReturnNode(self, node):
        node_id = self.add_node("ReturnNode")

        expr_id = self.visit(node.expression)
        self.add_edge(node_id, expr_id)

        return node_id

    def visit_ExprStmtNode(self, node):
        node_id = self.add_node("ExprStmtNode")

        expr_id = self.visit(node.expression)
        self.add_edge(node_id, expr_id)

        return node_id

    def visit_IfNode(self, node):
        node_id = self.add_node("IfNode")

        condition_id = self.visit(node.condition)
        then_id = self.visit(node.then_block)

        self.add_edge(node_id, condition_id)
        self.add_edge(node_id, then_id)

        if node.else_block is not None:
            else_id = self.visit(node.else_block)
            self.add_edge(node_id, else_id)

        return node_id

    def visit_WhileNode(self, node):
        node_id = self.add_node("WhileNode")

        condition_id = self.visit(node.condition)
        body_id = self.visit(node.body)

        self.add_edge(node_id, condition_id)
        self.add_edge(node_id, body_id)

        return node_id

    def visit_FuncDefNode(self, node):
        node_id = self.add_node("FuncDefNode\\n{}".format(node.name))

        params_id = self.add_node("Params\\n{}".format(", ".join(node.params)))
        body_id = self.visit(node.body)

        self.add_edge(node_id, params_id)
        self.add_edge(node_id, body_id)

        return node_id


def build_ast_graph(ast):
    builder = ASTGraphBuilder()
    return builder.build(ast)