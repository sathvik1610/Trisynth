"""
Unit Tests for IR Generation (Phase 5).

Verifies that the AST is correctly translated into Three-Address Code instructions.
"""
from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.ir.ir_gen import IRGenerator
from src.ir.instructions import OpCode

def generate_ir(source):
    tokens = Lexer(source).tokenize()
    ast_root = Parser(tokens).parse()
    generator = IRGenerator()
    return generator.generate(ast_root)

def test_arithmetic_ir():
    source = """
    void main() {
        int x = 1 + 2;
    }
    """
    ir = generate_ir(source)
    # Expected: FUNC_START, ADD t0 1 2, MOV x t0, FUNC_END
    assert len(ir) >= 3
    # Check for ADD presence
    assert any(instr.opcode == OpCode.ADD for instr in ir)
    # Check for MOV presence
    assert any(instr.opcode == OpCode.MOV for instr in ir)

def test_control_flow_if():
    source = """
    void main() {
        if (10 > 5) {
            print(1);
        }
    }
    """
    ir = generate_ir(source)
    # Should have GT, JMP_IF_FALSE, PRINT, LABEL
    opcodes = [instr.opcode for instr in ir]
    assert OpCode.GT in opcodes
    assert OpCode.JMP_IF_FALSE in opcodes
    assert OpCode.PRINT in opcodes
    assert OpCode.LABEL in opcodes

def test_while_loop():
    source = """
    void main() {
        while (1) {
            print(1);
        }
    }
    """
    ir = generate_ir(source)
    # LABEL (start), JMP_IF_FALSE, PRINT, JMP (back), LABEL (end)
    opcodes = [instr.opcode for instr in ir]
    labels = [instr for instr in ir if instr.opcode == OpCode.LABEL]
    jumps = [instr for instr in ir if instr.opcode == OpCode.JMP]
    
    assert len(labels) == 2 # Start and End
    assert len(jumps) == 1  # Loop back
    assert OpCode.JMP_IF_FALSE in opcodes
