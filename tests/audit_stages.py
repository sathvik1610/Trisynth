import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.ir_gen import IRGenerator
from src.optimization.optimizer import Optimizer
from src.frontend.token_type import TokenType

def print_separator(title):
    print(f"\n{'='*20} {title} {'='*20}")

def audit_compiler(source_code, name):
    print_separator(f"Starting Audit: {name}")
    print("Source Code:")
    print(source_code)
    
    # 1. Lexer
    print("\n--- [Stage 1] Lexer ---")
    try:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        print(f"✅ Tokenization Successful. Count: {len(tokens)}")
        # print([t.type.name for t in tokens])
    except Exception as e:
        print(f"❌ Lexer Failed: {e}")
        return

    # 2. Parser
    print("\n--- [Stage 2] Parser ---")
    try:
        parser = Parser(tokens)
        ast_root = parser.parse()
        print("✅ Parsing Successful.")
        # print(ast_root)
    except Exception as e:
        print(f"❌ Parser Failed: {e}")
        return

    # 3. Semantic Analysis
    print("\n--- [Stage 3] Semantic Analysis ---")
    try:
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast_root)
        print("✅ Semantic Analysis Passed.")
    except Exception as e:
        print(f"❌ Semantic Error: {e}")
        return # Depending on audit goals, maybe continue? No, semantic errors block IR.

    # 4. IR Generation
    print("\n--- [Stage 4] IR Generation ---")
    try:
        ir_gen = IRGenerator()
        ir = ir_gen.generate(ast_root)
        print(f"✅ IR Generated. Instructions: {len(ir)}")
        for i, instr in enumerate(ir):
            print(f"  {i:02}: {instr}")
    except Exception as e:
        print(f"❌ IR Generation Failed: {e}")
        return

    # 5. Optimization
    print("\n--- [Stage 5] Optimization ---")
    try:
        optimizer = Optimizer()
        opt_ir = optimizer.optimize(ir)
        print(f"✅ Optimization Compelte. Instructions: {len(opt_ir)}")
        print("Optimized IR:")
        for i, instr in enumerate(opt_ir):
            print(f"  {i:02}: {instr}")
            
        # Check basic sanity
        val_movs = [i for i in opt_ir if i.opcode.name == 'MOV']
        # If original had tons of dead code, this count should be lower.
    except Exception as e:
        print(f"❌ Optimization Failed: {e}")
        return

def run_audits():
    # Case 1: Complex Flow (Loops, Breaks, Arrays)
    code_complex = """
    void main() {
        int arr[5];
        for(int i=0; i<5; i=i+1) {
            if (i == 3) {
                break;
            }
            arr[i] = i * 2;
        }
    }
    """
    audit_compiler(code_complex, "Complex Flow & Arrays")

    # Case 2: Dead Code & Constant Folding
    code_opt = """
    void main() {
        int x = 10 + 20;
        int y = 5; 
        y = 100; // Overwrite, prev y unused? No, y is local var. 
        // Logic: if y is local var and unused, DCE might remove it ONLY if we track local var liveness.
        // Current DCE only tracks Temporaries (t0, t1). 
        // Let's test with temporaries.
        int z = 1 + 2; // z unused. tN generated. 
        // z maps to z_0. 
        // MOV z_0 3. 
        // is z_0 in used_vars? 
        // Only if some instruction uses it as arg1/arg2. 
        // If z is never read, z_0 is never in arg1/arg2.
        // So MOV z_0 3 should be removed?
        // Wait, dead_code.py logic: "if instr.result and instr.result not in used_vars".
        // Yes! It should remove user variables too if they are never read!
    }
    """
    audit_compiler(code_opt, "Optimization Capabilities")

    # Case 3: Shadowing Fix Regression
    code_shadow = """
    int g = 1;
    void main() {
        int g = 2;
        print(g);
    }
    """
    audit_compiler(code_shadow, "Variable Shadowing")

    # Case 4: ReadInt and Side Effects
    code_io = """
    void main() {
        int x = readInt();
        print(x);
    }
    """
    audit_compiler(code_io, "I/O Side Effects")

if __name__ == "__main__":
    run_audits()
