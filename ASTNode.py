from dataclasses import dataclass
from typing import List, Optional


# =========================
# NODO BASE
# =========================
class ASTNode:
    pass


# =========================
# NODOS GENERALES
# =========================
@dataclass
class ProgramNode(ASTNode):
    statements: List[ASTNode]


@dataclass
class BlockNode(ASTNode):
    statements: List[ASTNode]


# =========================
# LITERALES Y VARIABLES
# =========================
@dataclass
class NumberNode(ASTNode):
    value: str   # luego puedes convertir a int o float


@dataclass
class StringNode(ASTNode):
    value: str


@dataclass
class BoolNode(ASTNode):
    value: bool


@dataclass
class VariableNode(ASTNode):
    name: str


# =========================
# EXPRESIONES
# =========================
@dataclass
class BinOpNode(ASTNode):
    left: ASTNode
    operator: str
    right: ASTNode


@dataclass
class UnaryOpNode(ASTNode):
    operator: str
    operand: ASTNode


@dataclass
class FuncCallNode(ASTNode):
    name: str
    args: List[ASTNode]


# =========================
# SENTENCIAS
# =========================
@dataclass
class VarDeclNode(ASTNode):
    name: str
    value: ASTNode


@dataclass
class PrintNode(ASTNode):
    expression: ASTNode


@dataclass
class ReturnNode(ASTNode):
    expression: ASTNode


@dataclass
class ExprStmtNode(ASTNode):
    expression: ASTNode


@dataclass
class IfNode(ASTNode):
    condition: ASTNode
    then_block: BlockNode
    else_block: Optional[BlockNode]


@dataclass
class WhileNode(ASTNode):
    condition: ASTNode
    body: BlockNode


@dataclass
class FuncDefNode(ASTNode):
    name: str
    params: List[str]
    body: BlockNode

@dataclass
class AssignNode(ASTNode):
    name: str
    value: ASTNode