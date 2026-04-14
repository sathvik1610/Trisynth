import pytest
from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.ir_gen import IRGenerator
from src.ir.instructions import OpCode

def _gen_ir(code):
    ast = Parser(Lexer(code).tokenize()).parse()
    SemanticAnalyzer().analyze(ast)
    ir = IRGenerator().generate(ast)
    return ir

def test_basic_math_ir():
    ir = _gen_ir("void main() { int a = 5; int b = 10; int c = a + b; }")
    # Ensure constants load and ADD instruction is formed
    ops = [i.opcode for i in ir]
    assert OpCode.MOV in ops
    assert OpCode.ADD in ops

def test_if_statement_ir():
    ir = _gen_ir("void main() { int x = 5; if (x > 0) { x = 1; } else { x = 0; } }")
    ops = [i.opcode for i in ir]
    assert OpCode.GT in ops
    assert OpCode.JMP_IF_FALSE in ops
    assert OpCode.JMP in ops
    assert OpCode.LABEL in ops

def test_function_ir():
    ir = _gen_ir("int identity(int x) { return x; } void main() {}")
    ops = [i.opcode for i in ir]
    assert OpCode.FUNC_START in ops
    assert OpCode.LOAD_PARAM in ops
    assert OpCode.RETURN in ops

def test_array_ir():
    ir = _gen_ir("void main() { int arr[5]; arr[0] = 10; int x = arr[0]; }")
    ops = [i.opcode for i in ir]
    assert OpCode.ARR_DECL in ops
    assert OpCode.ASTORE in ops
    assert OpCode.ALOAD in ops
