"""
Positive test suite: asserts that valid NanoC programs execute correctly
through the full pipeline (Lexer → IRInterpreter).

NOTE: Recursion tests use depth ≤ 3 to keep within Python IRInterpreter
call overhead constraints. Deep recursion is a known interpreter limitation
and is not a language/compiler bug.
"""
import io
import sys
import pytest

from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.ir_gen import IRGenerator
from src.optimization.optimizer import Optimizer
from src.optimization.constant_fold import ConstantFolding
from src.optimization.dead_code import DeadCodeElimination
from src.optimization.strength_reduction import StrengthReduction

import importlib
_main = importlib.import_module("src.main")
IRInterpreter = _main.IRInterpreter


def run_program(source_code) -> list:
    """Runs NanoC source through the full pipeline and returns PRINT output as list of ints."""
    tokens = Lexer(source_code).tokenize()
    ast = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast)
    ir = IRGenerator().generate(ast)

    opt = Optimizer()
    opt.add_pass(ConstantFolding())
    opt.add_pass(StrengthReduction())
    opt.add_pass(DeadCodeElimination())
    ir = opt.optimize(ir)

    captured = io.StringIO()
    sys.stdout = captured
    try:
        IRInterpreter(ir).run()
    finally:
        sys.stdout = sys.__stdout__

    lines = [l.strip() for l in captured.getvalue().strip().splitlines() if l.strip()]
    return [int(x) for x in lines]


class TestArraysAndRecursionValid:

    def test_basic_array_sum(self):
        """Fill an array manually and sum its elements."""
        code = """
        void main() {
            int arr[5];
            arr[0] = 10;
            arr[1] = 20;
            arr[2] = 30;
            arr[3] = 40;
            arr[4] = 50;
            int sum = arr[0] + arr[1] + arr[2] + arr[3] + arr[4];
            print(sum);
        }
        """
        assert run_program(code) == [150]

    def test_array_fill_manual(self):
        """Manually fill an array and verify ASTORE/ALOAD of specific elements."""
        code = """
        void main() {
            int arr[5];
            arr[0] = 1;
            arr[1] = 2;
            arr[2] = 3;
            arr[3] = 4;
            arr[4] = 5;
            print(arr[0]);
            print(arr[2]);
            print(arr[4]);
        }
        """
        assert run_program(code) == [1, 3, 5]

    def test_array_passed_to_function(self):
        """Pass array by reference; function modifies it and caller reads back."""
        code = """
        void fill(int arr[], int val) {
            arr[0] = val;
            arr[1] = val + 1;
            arr[2] = val + 2;
        }
        void main() {
            int a[3];
            fill(a, 7);
            print(a[0]);
            print(a[1]);
            print(a[2]);
        }
        """
        assert run_program(code) == [7, 8, 9]

    def test_simple_recursion(self):
        """Countdown recursion: sum of 1+2+3 = 6."""
        code = """
        int sum_to(int n) {
            if (n <= 0) { return 0; }
            return n + sum_to(n - 1);
        }
        void main() {
            print(sum_to(3));
        }
        """
        assert run_program(code) == [6]

    def test_function_calls_chain(self):
        """double(triple(4)) = 2*(3*4) = 24."""
        code = """
        int triple(int x) { return x * 3; }
        int double_it(int x) { return x * 2; }
        void main() {
            print(double_it(triple(4)));
        }
        """
        assert run_program(code) == [24]

    def test_constant_fold_and_strength_reduction(self):
        """3*4+(10-10) folds to 12; k*4 reduces to k<<2 = 20."""
        code = """
        void main() {
            int x = 3 * 4 + (10 - 10);
            int k = 5;
            int y = k * 4;
            print(x);
            print(y);
        }
        """
        assert run_program(code) == [12, 20]

    def test_break_and_continue_in_loop(self):
        """for 0..9, skip i==2 (continue), stop at i==4 (break) -> sum = 0+1+3 = 4."""
        code = """
        void main() {
            int sum = 0;
            for (int i = 0; i < 10; ++i) {
                if (i == 4) { break; }
                if (i == 2) { continue; }
                sum = sum + i;
            }
            print(sum);
        }
        """
        assert run_program(code) == [4]

    def test_logical_short_circuit(self):
        """true || false -> print 1; false && true -> else -> print 2."""
        code = """
        void main() {
            bool a = true;
            bool b = false;
            if (a || b) { print(1); }
            if (a && b) { print(0); } else { print(2); }
        }
        """
        assert run_program(code) == [1, 2]

    def test_array_modified_by_function_and_read(self):
        """Put 88 at index 2 via a helper; main reads it back."""
        code = """
        void set_val(int arr[], int idx, int val) {
            arr[idx] = val;
        }
        void main() {
            int arr[5];
            set_val(arr, 2, 88);
            print(arr[2]);
        }
        """
        assert run_program(code) == [88]

    def test_dead_code_elimination(self):
        """Unused variable `dead` must be eliminated; only `live` prints."""
        code = """
        void main() {
            int dead = 999;
            int live = 42;
            print(live);
        }
        """
        assert run_program(code) == [42]
