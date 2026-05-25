from dataclasses import dataclass
from typing import List, Optional


# =========================
# NODO BASE
# =========================
class ASTNode:
    line: int = 0
    eval_type: Optional[str] = None


# =========================
# NODOS GENERALES
# =========================
@dataclass
class ProgramNode(ASTNode):
    statements: List[ASTNode]
    line: int = 0
    eval_type: Optional[str] = None


@dataclass
class BlockNode(ASTNode):
    statements: List[ASTNode]
    line: int = 0
    eval_type: Optional[str] = None


# =========================
# LITERALES Y VARIABLES
# =========================
@dataclass
class NumberNode(ASTNode):
    value: str
    line: int = 0
    eval_type: Optional[str] = None


@dataclass
class StringNode(ASTNode):
    value: str
    line: int = 0
    eval_type: Optional[str] = None


@dataclass
class BoolNode(ASTNode):
    value: bool
    line: int = 0
    eval_type: Optional[str] = None

@dataclass
class VariableNode(ASTNode):
    name: str
    line: int = 0
    eval_type: Optional[str] = None


# =========================
# EXPRESIONES
# =========================
@dataclass
class BinOpNode(ASTNode):
    left: ASTNode
    operator: str
    right: ASTNode
    line: int = 0
    eval_type: Optional[str] = None


@dataclass
class UnaryOpNode(ASTNode):
    operator: str
    operand: ASTNode
    line: int = 0
    eval_type: Optional[str] = None

@dataclass
class FuncCallNode(ASTNode):
    name: str
    args: List[ASTNode]
    line: int = 0
    eval_type: Optional[str] = None


# =========================
# SENTENCIAS
# =========================
@dataclass
class VarDeclNode(ASTNode):
    name: str
    value: ASTNode
    line: int = 0
    eval_type: Optional[str] = None

@dataclass
class PrintNode(ASTNode):
    expression: ASTNode
    line: int = 0
    eval_type: Optional[str] = None


@dataclass
class ReturnNode(ASTNode):
    expression: ASTNode
    line: int = 0
    eval_type: Optional[str] = None


@dataclass
class ExprStmtNode(ASTNode):
    expression: ASTNode
    line: int = 0
    eval_type: Optional[str] = None

@dataclass
class IfNode(ASTNode):
    condition: ASTNode
    then_block: BlockNode
    else_block: Optional[BlockNode] = None
    line: int = 0
    eval_type: Optional[str] = None

@dataclass
class WhileNode(ASTNode):
    condition: ASTNode
    body: BlockNode
    line: int = 0
    eval_type: Optional[str] = None
    
@dataclass
class FuncDefNode(ASTNode):
    name: str
    params: List[str]
    body: BlockNode
    line: int = 0
    eval_type: Optional[str] = None
