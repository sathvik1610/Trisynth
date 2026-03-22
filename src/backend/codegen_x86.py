from typing import List
from src.ir.instructions import Instruction, OpCode
from src.backend.common.stack_frame import StackFrame


class X86Generator:
    """
    Generates x86-64 Assembly (NASM) from IR.
    Strategy: Stack Machine (No register allocation).
    """

    def __init__(self):
        self.output: List[str] = []
        self.current_frame = None
        self._pending_params = []  # Buffer for PARAM instructions

        # Strings data section
        self.strings = []

    def generate(self, instructions: List[Instruction]) -> str:
        self._emit_header()

        current_func_instrs = []
        in_function = False

        for instr in instructions:
            if instr.opcode == OpCode.FUNC_START:
                in_function = True
                current_func_instrs = [instr]
            elif instr.opcode == OpCode.FUNC_END:
                current_func_instrs.append(instr)
                self._compile_function(current_func_instrs)
                in_function = False
                current_func_instrs = []
            elif in_function:
                current_func_instrs.append(instr)
            else:
                pass

        self._emit_footer()
        return "\n".join(self.output)

    def _compile_function(self, instrs: List[Instruction]):
        func_name = instrs[0].arg1

        # 1. Analyze Frame
        frame = StackFrame()
        for instr in instrs:
            if instr.opcode == OpCode.ARR_DECL:
                frame.allocate(instr.result, size=instr.arg1 * 8)
            elif instr.opcode == OpCode.LOAD_PARAM_REF:
                frame.allocate(instr.result, is_ref=True)
            elif instr.result and instr.opcode != OpCode.ARR_DECL:
                frame.allocate(instr.result)

        frame.finalize()
        self.current_frame = frame

        # 2. Emit Prologue
        self._emit(f"; --- Function {func_name} ---")
        self._emit(f"global {func_name}")
        self._emit(f"{func_name}:")
        self._emit("    push rbp")
        self._emit("    mov rbp, rsp")
        if frame.total_size > 0:
            self._emit(f"    sub rsp, {frame.total_size}")

        # 3. Emit Body
        for instr in instrs[1:-1]:  # Skip FUNC_START/END
            self._emit_instruction(instr)

        # 4. Emit Epilogue
        self._emit(f".exit_{func_name}:")
        self._emit("    mov rsp, rbp")
        self._emit("    pop rbp")
        self._emit("    ret")

    def _emit_instruction(self, instr: Instruction):
        self._emit(f"    ; {instr}")

        if instr.opcode == OpCode.MOV:
            self._load_to_rax(instr.arg1)
            self._store_rax(instr.result)

        elif instr.opcode == OpCode.ADD:
            self._load_to_rax(instr.arg1)
            self._emit(f"    mov rbx, rax")
            op2 = self._resolve_operand(instr.arg2)
            self._emit(f"    add rbx, {op2}")
            self._emit(f"    mov rax, rbx")
            self._store_rax(instr.result)

        elif instr.opcode == OpCode.SUB:
            self._load_to_rax(instr.arg1)
            op2 = self._resolve_operand(instr.arg2)
            self._emit(f"    sub rax, {op2}")
            self._store_rax(instr.result)

        elif instr.opcode == OpCode.MUL:
            self._load_to_rax(instr.arg1)
            op2 = self._resolve_operand(instr.arg2)
            self._emit(f"    imul rax, {op2}")
            self._store_rax(instr.result)

        elif instr.opcode == OpCode.DIV:
            self._load_to_rax(instr.arg1)
            self._emit("    cqo")
            op2 = instr.arg2
            if isinstance(op2, int):
                self._emit(f"    mov rcx, {op2}")
                self._emit("    idiv rcx")
            else:
                src = self._resolve_operand(op2)
                self._emit(f"    idiv qword {src}")
            self._store_rax(instr.result)

        elif instr.opcode == OpCode.MOD:
            self._load_to_rax(instr.arg1)
            self._emit("    cqo")
            op2 = instr.arg2
            if isinstance(op2, int):
                self._emit(f"    mov rcx, {op2}")
                self._emit("    idiv rcx")
            else:
                src = self._resolve_operand(op2)
                self._emit(f"    idiv qword {src}")
            self._emit(f"    mov rax, rdx")
            self._store_rax(instr.result)

        elif instr.opcode == OpCode.LSHIFT:
            count = instr.arg2
            self._load_to_rax(instr.arg1)
            if isinstance(count, int):
                self._emit(f"    shl rax, {count}")
            else:
                src_count = self._resolve_operand(count)
                self._emit(f"    mov rcx, {src_count}")
                self._emit("    shl rax, cl")   # FIX: was "shl rax, cls" (typo)
            self._store_rax(instr.result)

        elif instr.opcode == OpCode.RSHIFT:
            count = instr.arg2
            self._load_to_rax(instr.arg1)
            if isinstance(count, int):
                self._emit(f"    sar rax, {count}")
            else:
                src_count = self._resolve_operand(count)
                self._emit(f"    mov rcx, {src_count}")
                self._emit("    sar rax, cl")
            self._store_rax(instr.result)

        elif instr.opcode in (OpCode.LT, OpCode.GT, OpCode.EQ, OpCode.NEQ, OpCode.LTE, OpCode.GTE):
            self._load_to_rax(instr.arg1)
            op2 = self._resolve_operand(instr.arg2)
            self._emit(f"    cmp rax, {op2}")
            cc_map = {
                OpCode.LT: "setl", OpCode.GT: "setg", OpCode.EQ: "sete",
                OpCode.NEQ: "setne", OpCode.LTE: "setle", OpCode.GTE: "setge"
            }
            cc = cc_map[instr.opcode]
            self._emit(f"    {cc} al")
            self._emit("    movzx rax, al")
            self._store_rax(instr.result)

        elif instr.opcode == OpCode.PRINT:
            self._load_to_rax(instr.arg1)
            self._emit("    mov rsi, rax")
            self._emit("    lea rdi, [rel fmt_int]")
            self._emit("    xor rax, rax")
            self._emit("    mov rbx, rsp")   # save rsp
            self._emit("    and rsp, -16")   # align
            self._emit("    call printf")
            self._emit("    mov rsp, rbx")   # restore rsp

        elif instr.opcode == OpCode.RETURN:
            if instr.arg1 is not None:
                self._load_to_rax(instr.arg1)
            self._emit("    mov rsp, rbp")
            self._emit("    pop rbp")
            self._emit("    ret")

        elif instr.opcode == OpCode.LABEL:
            self._emit(f"{instr.arg1}:")

        elif instr.opcode == OpCode.JMP:
            self._emit(f"    jmp {instr.arg1}")

        elif instr.opcode == OpCode.JMP_IF_FALSE:
            self._load_to_rax(instr.arg1)
            self._emit("    cmp rax, 0")
            self._emit(f"    je {instr.arg2}")

        # --- Memory / Arrays ---
        elif instr.opcode == OpCode.ARR_DECL:
            pass  # Already handled in frame analysis

        elif instr.opcode == OpCode.ALOAD:
            idx_val = instr.arg2

            self._load_to_rax(idx_val)          # RAX = index
            self._emit("    imul rax, 8")        # Scale by 8 bytes

            arr_base = self.current_frame.get_offset(instr.arg1)

            if self.current_frame.is_reference(instr.arg1):
                self._emit(f"    mov rcx, [rbp - {arr_base}]")
            else:
                self._emit(f"    lea rcx, [rbp - {arr_base}]")

            self._emit("    add rcx, rax")
            self._emit("    mov rdx, [rcx]")
            self._store_rax(instr.result, src_reg="rdx")

        elif instr.opcode == OpCode.ASTORE:
            idx_val = instr.arg2
            self._load_to_rax(idx_val)
            self._emit("    imul rax, 8")

            arr_base = self.current_frame.get_offset(instr.arg1)
            if self.current_frame.is_reference(instr.arg1):
                self._emit(f"    mov rcx, [rbp - {arr_base}]")
            else:
                self._emit(f"    lea rcx, [rbp - {arr_base}]")

            self._emit("    add rcx, rax")

            val = instr.result  # ASTORE reuses result field for value

            self._emit(f"    push rcx")     # Save address
            self._load_to_rax(val)          # RAX = value
            self._emit("    mov r9, rax")   # Save value away from stack ops
            self._emit("    pop rcx")       # Restore address
            self._emit("    mov [rcx], r9")

        # --- Functions ---
        elif instr.opcode == OpCode.PARAM:
            self._pending_params.append((instr.arg1, False))

        elif instr.opcode == OpCode.PARAM_REF:
            self._pending_params.append((instr.arg1, True))

        elif instr.opcode == OpCode.CALL:
            func_name = instr.arg1
            num_args = instr.arg2

            args_to_push = self._pending_params[-num_args:]
            self._pending_params = self._pending_params[:-num_args]

            for arg, is_ref in reversed(args_to_push):
                if is_ref:
                    arr_base = self.current_frame.get_offset(arg)
                    if self.current_frame.is_reference(arg):
                        self._emit(f"    mov rax, [rbp - {arr_base}]")
                    else:
                        self._emit(f"    lea rax, [rbp - {arr_base}]")
                    self._emit("    push rax")
                else:
                    self._load_to_rax(arg)
                    self._emit("    push rax")

            self._emit(f"    call {func_name}")

            if num_args > 0:
                self._emit(f"    add rsp, {num_args * 8}")

            self._store_rax(instr.result)

        elif instr.opcode == OpCode.LOAD_PARAM:
            idx = instr.arg1
            offset = 16 + idx * 8
            self._emit(f"    mov rax, [rbp + {offset}]")
            self._store_rax(instr.result)

        elif instr.opcode == OpCode.LOAD_PARAM_REF:
            idx = instr.arg1
            offset = 16 + idx * 8
            self._emit(f"    mov rax, [rbp + {offset}]")
            self._store_rax(instr.result)

    def _resolve_operand(self, arg):
        if isinstance(arg, int):
            return str(arg)
        elif isinstance(arg, str):
            offset = self.current_frame.get_offset(arg)
            return f"[rbp - {offset}]"
        else:
            raise Exception(f"Unknown arg type: {arg}")

    def _load_to_rax(self, arg):
        src = self._resolve_operand(arg)
        self._emit(f"    mov rax, {src}")
        return "rax"

    def _store_rax(self, dest_var, src_reg="rax"):
        """Stores a register (default RAX) into the stack slot of dest_var."""
        if dest_var is None:   # FIX: guard against void/no-result instructions
            return
        offset = self.current_frame.get_offset(dest_var)
        self._emit(f"    mov [rbp - {offset}], {src_reg}")

    def _emit(self, line: str):
        self.output.append(line)

    def _emit_header(self):
        self.output.append("section .data")
        self.output.append('    fmt_int db "%ld", 10, 0')
        self.output.append("")
        self.output.append("section .text")
        self.output.append("    extern printf")
        self.output.append("    extern scanf")
        self.output.append("")

    def _emit_footer(self):
        self._emit("")
        self._emit("section .note.GNU-stack noalloc noexec nowrite progbits")
