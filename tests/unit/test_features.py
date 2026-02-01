import pytest
from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.ir_gen import IRGenerator
from src.ir.instructions import OpCode

def generate_ir(code):
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    ir_gen = IRGenerator()
    return ir_gen.generate(ast)

def test_array_declaration_and_access():
    code = """
    int x[10];
    void main() {
        x[0] = 5;
        int y = x[0];
    }
    """
    ir = generate_ir(code)
    # Check for ASTORE and ALOAD
    opcodes = [instr.opcode for instr in ir]
    assert OpCode.ASTORE in opcodes
    assert OpCode.ALOAD in opcodes

def test_for_loop():
    code = """
    void main() {
        int sum = 0;
        for (int i = 0; i < 10; i = i + 1) {
            sum = sum + i;
        }
    }
    """
    ir = generate_ir(code)
    # Check for labels and jumps logic
    labels = [instr for instr in ir if instr.opcode == OpCode.LABEL]
    jumps = [instr for instr in ir if instr.opcode in (OpCode.JMP, OpCode.JMP_IF_FALSE)]
    
    # Structure: Init -> LabelStart -> Cond -> JmpEnd -> Body -> LabelUpdate -> Update -> JmpStart -> LabelEnd
    # Expect 3 labels per loop
    assert len(labels) >= 3 
    assert len(jumps) >= 2

def test_logical_operators():
    code = """
    void main() {
        bool a = true;
        bool b = false;
        bool c = a && b;
        bool d = a || b;
    }
    """
    ir = generate_ir(code)
    # Short circuiting generates labels and jumps
    opcodes = [instr.opcode for instr in ir]
    # We shouldn't see AND/OR opcodes because they are compiled to control flow
    assert OpCode.JMP_IF_FALSE in opcodes
    assert OpCode.LABEL in opcodes

def test_break_continue():
    code = """
    void main() {
        while(true) {
            break;
        }
        while(true) {
            continue;
        }
    }
    """
    ir = generate_ir(code)
    # Should compile without error and generate JMPs
    jumps = [instr for instr in ir if instr.opcode == OpCode.JMP]
    # One JMP for break, One JMP for continue, plus logic jumps
    assert len(jumps) >= 2

def test_read_int():
    code = """
    void main() {
        int x = readInt();
    }
    """
    ir = generate_ir(code)
    # Check for CALL and PARAM (though readInt has 0 params)
    opcodes = [instr.opcode for instr in ir]
    assert OpCode.CALL in opcodes
    # Verify call target is readInt
    call_instr = [instr for instr in ir if instr.opcode == OpCode.CALL][0]
    assert call_instr.arg1 == 'readInt'
