"""Regression tests: optimized IR must behave exactly like unoptimized IR on a 64-bit machine.

Reference semantics (what x86-64 / RISC-V do): signed 64-bit wraparound, division and modulo
truncating toward zero, arithmetic right shift. A small reference IR evaluator implements them
so that "optimized vs unoptimized" is compared under hardware rules, not Python's.
"""
import shutil
import subprocess

import pytest

from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.ir_gen import IRGenerator
from src.ir.instructions import Instruction, OpCode
from src.optimization.strength_reduction import StrengthReduction
from src.optimization.cse import CommonSubexpressionElimination
from src.optimization.copy_propagation import CopyPropagation
from src.optimization.constant_fold import ConstantFolding
from src.optimization.dead_code import DeadCodeElimination

INT_MIN = -(1 << 63)
INT_MAX = (1 << 63) - 1


# ---------------------------------------------------------------- reference semantics

def wrap(v):
    v &= (1 << 64) - 1
    return v - (1 << 64) if v > INT_MAX else v

def c_div(a, b):
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q

def c_mod(a, b):
    return a - b * c_div(a, b)


def run_ir(ir, inputs=(), env=None):
    """Executes the IR of `main` with hardware integer semantics; returns the printed values."""
    env = dict(env or {})
    inputs = list(inputs)
    out = []
    labels = {i.arg1: n for n, i in enumerate(ir) if i.opcode == OpCode.LABEL}
    pc = next(n for n, i in enumerate(ir) if i.opcode == OpCode.FUNC_START and i.arg1 == "main")

    def val(a):
        return env[a] if isinstance(a, str) else a

    binops = {
        OpCode.ADD: lambda a, b: wrap(a + b),
        OpCode.SUB: lambda a, b: wrap(a - b),
        OpCode.MUL: lambda a, b: wrap(a * b),
        OpCode.DIV: c_div,
        OpCode.MOD: c_mod,
        OpCode.LSHIFT: lambda a, b: wrap(a << (b & 63)),
        OpCode.RSHIFT: lambda a, b: a >> (b & 63),
        OpCode.LT: lambda a, b: int(a < b), OpCode.GT: lambda a, b: int(a > b),
        OpCode.LTE: lambda a, b: int(a <= b), OpCode.GTE: lambda a, b: int(a >= b),
        OpCode.EQ: lambda a, b: int(a == b), OpCode.NEQ: lambda a, b: int(a != b),
    }

    while pc < len(ir):
        i = ir[pc]
        op = i.opcode
        if op in binops:
            env[i.result] = binops[op](val(i.arg1), val(i.arg2))
        elif op == OpCode.MOV:
            env[i.result] = val(i.arg1)
        elif op == OpCode.CALL and i.arg1 == "readInt":
            env[i.result] = inputs.pop(0)
        elif op == OpCode.PRINT:
            out.append(val(i.arg1))
        elif op == OpCode.JMP:
            pc = labels[i.arg1]
        elif op == OpCode.JMP_IF_FALSE:
            if val(i.arg1) == 0:
                pc = labels[i.arg2]
        elif op in (OpCode.FUNC_END, OpCode.RETURN):
            break
        pc += 1
    return out


# ---------------------------------------------------------------- compiler helpers

def frontend(source):
    ast = Parser(Lexer(source).tokenize()).parse()
    SemanticAnalyzer().analyze(ast)
    return IRGenerator().generate(ast)

def optimize(ir):
    """The same pass order main.py uses."""
    for opt_pass in (StrengthReduction(), CommonSubexpressionElimination(), CopyPropagation(),
                     ConstantFolding(), CommonSubexpressionElimination(), DeadCodeElimination()):
        ir = opt_pass.run(ir)
    return ir

def fold(opcode, a, b):
    out = ConstantFolding().run([Instruction(opcode, arg1=a, arg2=b, result="t0")])
    return out[0]


# ---------------------------------------------------------------- 1. constant folding: wraparound

@pytest.mark.parametrize("opcode, a, b, expected", [
    (OpCode.ADD, INT_MAX, 1, INT_MIN),
    (OpCode.ADD, INT_MIN, -1, INT_MAX),
    (OpCode.SUB, INT_MIN, 1, INT_MAX),
    (OpCode.SUB, INT_MAX, -1, INT_MIN),
    (OpCode.MUL, 1 << 32, 1 << 32, 0),
    (OpCode.MUL, INT_MAX, 2, -2),
    (OpCode.MUL, INT_MIN, -1, INT_MIN),
    (OpCode.MUL, 3037000500, 3037000500, wrap(3037000500 * 3037000500)),
    (OpCode.LSHIFT, 1, 63, INT_MIN),
    (OpCode.LSHIFT, 3, 62, wrap(3 << 62)),
    (OpCode.LSHIFT, INT_MAX, 1, -2),
    (OpCode.ADD, 5, 10, 15),
])
def test_fold_wraps_to_signed_64_bit(opcode, a, b, expected):
    folded = fold(opcode, a, b)
    assert folded.opcode == OpCode.MOV
    assert folded.arg1 == expected
    assert INT_MIN <= folded.arg1 <= INT_MAX


# ---------------------------------------------------------------- 2. folding: C division / modulo

@pytest.mark.parametrize("a, b, quotient, remainder", [
    (7, 2, 3, 1),
    (-7, 2, -3, -1),
    (7, -2, -3, 1),
    (-7, -2, 3, -1),
    (-7, 3, -2, -1),
    (7, -3, -2, 1),
    (0, 5, 0, 0),
    (-1, 2, 0, -1),
    (INT_MIN, 2, INT_MIN // 2, 0),
    (INT_MIN, INT_MAX, -1, -1),
    (INT_MAX, -1, -INT_MAX, 0),
])
def test_fold_div_mod_truncate_toward_zero(a, b, quotient, remainder):
    assert fold(OpCode.DIV, a, b).arg1 == quotient
    assert fold(OpCode.MOD, a, b).arg1 == remainder
    assert quotient * b + remainder == a        # the C identity (a/b)*b + a%b == a


@pytest.mark.parametrize("opcode, a, b", [
    (OpCode.DIV, 5, 0),
    (OpCode.MOD, 5, 0),
    (OpCode.DIV, INT_MIN, -1),      # traps on x86, so it must stay a runtime operation
    (OpCode.MOD, INT_MIN, -1),
    (OpCode.LSHIFT, 1, 64),         # shift counts the CPU would mask are not folded
    (OpCode.LSHIFT, 1, -1),
    (OpCode.RSHIFT, 8, 64),
    (OpCode.RSHIFT, 8, -1),
])
def test_fold_leaves_trapping_or_masked_cases_alone(opcode, a, b):
    assert fold(opcode, a, b).opcode == opcode


def test_fold_rshift_is_arithmetic():
    assert fold(OpCode.RSHIFT, -7, 1).arg1 == -4
    assert fold(OpCode.RSHIFT, 7, 1).arg1 == 3


# ---------------------------------------------------------------- 3. strength reduction of signed division

def test_div_by_power_of_two_no_longer_a_bare_shift():
    out = StrengthReduction().run([Instruction(OpCode.DIV, arg1="x", arg2=4, result="t0")])
    assert OpCode.DIV not in [i.opcode for i in out]
    assert out[-1].opcode == OpCode.RSHIFT and out[-1].arg2 == 2 and out[-1].result == "t0"
    assert len(out) > 1                                          # bias is computed first

def test_div_with_constant_dividend_is_left_to_folding():
    out = StrengthReduction().run([Instruction(OpCode.DIV, arg1=-7, arg2=2, result="t0")])
    assert [i.opcode for i in out] == [OpCode.DIV]

def test_div_by_non_power_of_two_untouched():
    out = StrengthReduction().run([Instruction(OpCode.DIV, arg1="x", arg2=6, result="t0")])
    assert [i.opcode for i in out] == [OpCode.DIV]

DIVIDENDS = sorted({INT_MIN, INT_MIN + 1, INT_MAX, INT_MAX - 1, 0, 1, -1,
                    *range(-17, 18), 1 << 40, -(1 << 40), (1 << 40) + 1, -(1 << 40) - 1})

@pytest.mark.parametrize("k", list(range(1, 63)))
def test_signed_div_by_power_of_two_matches_hardware(k):
    d = 1 << k
    plain = [Instruction(OpCode.FUNC_START, arg1="main"),
             Instruction(OpCode.DIV, arg1="x", arg2=d, result="r"),
             Instruction(OpCode.PRINT, arg1="r"),
             Instruction(OpCode.FUNC_END, arg1="main")]
    reduced = StrengthReduction().run(plain)
    piped = optimize(plain)
    for x in DIVIDENDS + [d - 1, -d + 1, d, -d, d + 1, -d - 1]:
        want = [c_div(x, d)]
        assert run_ir(plain, env={"x": x}) == want
        assert run_ir(reduced, env={"x": x}) == want, f"x={x} k={k}"
        assert run_ir(piped, env={"x": x}) == want, f"x={x} k={k} (full pipeline)"

def test_negative_division_example_from_the_bug():
    plain = [Instruction(OpCode.FUNC_START, arg1="main"),
             Instruction(OpCode.DIV, arg1="x", arg2=2, result="r"),
             Instruction(OpCode.PRINT, arg1="r"),
             Instruction(OpCode.FUNC_END, arg1="main")]
    assert run_ir(StrengthReduction().run(plain), env={"x": -7}) == [-3]   # a bare >> 1 gives -4


# ---------------------------------------------------------------- 4. whole programs: optimized == unoptimized

PROGRAM = """
void main() {
    int a = readInt();
    print(a / 2);
    print(a / 8);
    print(a / 3);
    print(a % 3);
    print(a % 8);
    print(a * 8);
    print(a * a);
    print(a << 3);
    print(a + 1);
    print(a - 1);
    print((0 - 7) / 2);
    print((0 - 7) % 3);
    print(7 % (0 - 3));
    print(9223372036854775807 + 1);
    int big = 4294967296;
    print(big * big);
    print(big * big * 2);
    print(big * (big - 1));
    print(1 << 63);
}
"""

def expected_for(a):
    big = 1 << 32
    return [c_div(a, 2), c_div(a, 8), c_div(a, 3), c_mod(a, 3), c_mod(a, 8),
            wrap(a * 8), wrap(a * a), wrap(a << 3), wrap(a + 1), wrap(a - 1),
            -3, -1, 1, INT_MIN, 0, 0, wrap(big * (big - 1)), INT_MIN]

INPUTS = [0, 1, -1, 7, -7, 8, -8, 9, -9, 1000003, -1000003, INT_MAX, INT_MIN, INT_MIN + 1]

@pytest.mark.parametrize("a", INPUTS)
def test_program_optimized_matches_unoptimized_and_c_semantics(a):
    raw = frontend(PROGRAM)
    opt = optimize(raw)
    assert run_ir(raw, [a]) == expected_for(a)
    assert run_ir(opt, [a]) == run_ir(raw, [a])

def test_constant_expressions_fully_folded_with_c_semantics():
    src = """
    void main() {
        print((0 - 7) / 2);
        print((0 - 7) % 3);
        print(9223372036854775807 + 1);
    }
    """
    opt = optimize(frontend(src))
    assert run_ir(opt) == [-3, -1, INT_MIN]
    assert OpCode.DIV not in [i.opcode for i in opt] and OpCode.MOD not in [i.opcode for i in opt]

def test_loop_with_negative_division_matches():
    src = """
    void main() {
        int n = readInt();
        int i = 0;
        while (i < 5) {
            print(n / 4);
            n = n - 3;
            i = i + 1;
        }
    }
    """
    raw = frontend(src)
    opt = optimize(raw)
    for start in (-20, -1, 0, 1, 20):
        want, n = [], start
        for _ in range(5):
            want.append(c_div(n, 4))
            n -= 3
        assert run_ir(raw, [start]) == want
        assert run_ir(opt, [start]) == want


# ---------------------------------------------------------------- 5. real x86-64 execution (skipped if no toolchain)

def _x86_tools():
    """Returns the command prefix for running nasm/gcc/the program, or None. Uses WSL on Windows."""
    for prefix in ([], ["wsl"]):
        if prefix and shutil.which("wsl") is None:
            continue
        if not prefix and shutil.which("nasm") is None:
            continue
        try:
            subprocess.run(prefix + ["sh", "-c", "nasm -v && gcc --version"], capture_output=True, check=True, timeout=30)
            return prefix
        except Exception:
            continue
    return None

@pytest.fixture(scope="module")
def native_program(tmp_path_factory):
    import platform
    if platform.system() == "Windows" and shutil.which("wsl") is None:
        pytest.skip("needs Linux or WSL with nasm and gcc")
    prefix = _x86_tools()
    if prefix is None:
        pytest.skip("nasm/gcc not available")
    from src.backend.codegen_x86 import X86Generator
    work = tmp_path_factory.mktemp("native")
    (work / "output.asm").write_text(X86Generator().generate(optimize(frontend(PROGRAM))))
    try:
        subprocess.run(prefix + ["sh", "-c", "nasm -f elf64 output.asm -o output.o && gcc output.o -o program -no-pie"],
                       cwd=work, capture_output=True, check=True, timeout=120)
    except subprocess.CalledProcessError as e:
        pytest.fail(f"assembling failed: {e.stderr.decode(errors='replace')}")
    return prefix, work

@pytest.mark.parametrize("a", INPUTS)
def test_native_x86_matches_c_semantics(native_program, a):
    prefix, work = native_program
    run = subprocess.run(prefix + ["./program"], cwd=work, input=f"{a}\n", capture_output=True, text=True, timeout=60)
    assert [int(x) for x in run.stdout.split()] == expected_for(a)
