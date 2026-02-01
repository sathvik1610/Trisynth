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
        # ... (rest same)

    # ...

    def _store_rax(self, dest_var, src_reg="rax"):
        """Stores Register (default RAX) into stack slot of dest_var."""
        if dest_var is None: return 
        offset = self.current_frame.get_offset(dest_var)
        self._emit(f"    mov [rbp - {offset}], {src_reg}")

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
            if instr.result:
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
        for instr in instrs[1:-1]: # Skip FUNC_START/END
            self._emit_instruction(instr)
            
        # 4. Emit Epilogue
        self._emit(f".exit_{func_name}:")
        self._emit("    mov rsp, rbp")
        self._emit("    pop rbp")
        self._emit("    ret")

    def _emit_instruction(self, instr: Instruction):
        self._emit(f"    ; {instr}")
        
        if instr.opcode == OpCode.MOV:
            val = self._load_to_rax(instr.arg1)
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
                 self._emit("    shl rax, cls") # typo fix?
                 self._emit("    shl rax, cl") 
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
            val = self._load_to_rax(instr.arg1)
            self._emit("    mov rsi, rax")
            self._emit("    lea rdi, [fmt_int]")
            self._emit("    xor rax, rax")
            self._emit("    call printf")
            
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
        elif instr.opcode == OpCode.ALOAD:
            # ALOAD dest, arr_name, index
            # addr = rbp - offset_base + index*8
            # But wait, offset_base in StackFrame is the "bottom" of the array block?
            # Or the top?
            # StackFrame: allocate(16) -> current+=16. Offset=16. 
            # Slot is [rbp-16] to [rbp-0].
            # [rbp-16] is lowest address. [rbp-8] is highest.
            # Array[0] is at lowest address.
            # So Base = rbp - offset.
            
            idx_val = instr.arg2 # Register/Imm/Var
            
            # Load index to RAX
            self._load_to_rax(idx_val) # RAX = index
            self._emit("    imul rax, 8") # Scale
            
            arr_base = self.current_frame.get_offset(instr.arg1)
            # Address = rbp - arr_base + RAX
            self._emit(f"    lea rcx, [rbp - {arr_base}]")
            self._emit("    add rcx, rax")
            self._emit("    mov rdx, [rcx]")
            self._store_rax(instr.result, src_reg="rdx")

        elif instr.opcode == OpCode.ASTORE:
            # ASTORE arr_name, index, value
            
            idx_val = instr.arg2
            self._load_to_rax(idx_val)
            self._emit("    imul rax, 8")
            
            arr_base = self.current_frame.get_offset(instr.arg1)
            self._emit(f"    lea rcx, [rbp - {arr_base}]")
            self._emit("    add rcx, rax")
            
            # Load value to store
            val = instr.result # ASTORE reuses result field for value
            # Move value to RDX (since RAX used for address calc? No, we used RCX for addr)
            # But _load_to_rax clobbers RAX.
            # So:
            # 1. Calc Addr in RCX
            # 2. Load Val in RAX
            # 3. Store RAX to [RCX]
            # Valid.
            
            # wait, _load_to_rax might clobber RCX if it uses it for intermediate? 
            # My current _load_to_rax doesn't use RCX.
            
            # HOWEVER, safest to maximize separation.
            # Let's verify _load_to_rax implementation...
            # It just does mov rax, [rbp-X] or imm. Safe.
            
            self._emit(f"    push rcx") # Save address
            self._load_to_rax(val)      # RAX = value
            self._emit("    pop rcx")   # Restore address
            self._emit("    mov [rcx], rax")

        # --- Functions ---
        elif instr.opcode == OpCode.PARAM:
            # PARAM val
            # Push to stack.
            # Note: We push Right-to-Left? 
            # IR Gen emits PARAM a, PARAM b, CALL.
            # If we push a, push b. Stack: [b, a].
            # Callee: [rbp+16] -> b. [rbp+24] -> a.
            # This is Reverse Order.
            # Standard C: [rbp+16] -> first arg.
            # So we need [rbp+16] -> a.
            # This means we should have pushed b THEN a.
            # But IR Gen emits PARAM a, PARAM b.
            # So we are pushing in wrong order for standard C.
            # But for INTERNAL functions, as long as LOAD_PARAM matches, it's fine.
            # LOAD_PARAM 0 reads [rbp+16 + 0*8].
            # If we pushed a, then b. Stack top is b.
            # [rbp+16] is b.
            # So LOAD_PARAM 0 gets b (the second param).
            # LOAD_PARAM 1 gets a (the first param).
            # This reverses arguments!
            # FIX: LOAD_PARAM logic or Push logic.
            # Simplest: Adjust LOAD_PARAM to read downwards? No, args are positive.
            # We must Push in Reverse IR Order?
            # Or IR Gen should emit PARAMs in reverse?
            # Or LOAD_PARAM i maps to `rbp + 16 + (N-1-i)*8`?
            # We don't know N (arg count) easily in LOAD_PARAM.
            # We DO know N in CALL.
            # But PARAM instructions handle the pushing.
            # ISSUE: We need to push args in reverse order of IR?
            # Or we accept that internal functions have inverted args on stack?
            # If `main` calls `foo(1, 2)`.
            # IR: PARAM 1, PARAM 2.
            # Stack: Push 1, Push 2. Top: 2.
            # Callee `foo(a, b)`:
            # LOAD_PARAM 0 (a) -> Reads [rbp+16] -> 2.
            # LOAD_PARAM 1 (b) -> Reads [rbp+24] -> 1.
            # So `a=2`, `b=1`. Swapped.
            # Critical Fix: IR Gen should emit params in reverse?
            # Or Backend buffers PARAMs and pushes on CALL?
            # Buffering is safest for Backend.
            # Let's Buffer PARAMs.
            
            self._pending_params.append(instr.arg1)
            # Don't emit anything yet.

        elif instr.opcode == OpCode.CALL:
            # CALL func_name, num_args
            # Flush params in REVERSE order.
            
            # self._pending_params should have num_args items.
            # We pop/clear them.
            
            func_name = instr.arg1
            num_args = instr.arg2
            
            # Ensure we take exactly num_args from pending (if nested calls exist?)
            # Since linear IR, `PARAM; CALL;` is standard.
            # Pending should match.
            
            args_to_push = self._pending_params[-num_args:]
            self._pending_params = self._pending_params[:-num_args]
            
            # Push in Reverse (Last arg pushed first -> Highest Address)
            # Wait. C Conv: Last arg pushed first.
            # foo(1, 2). Push 2. Push 1.
            # Stack: [1, 2]. Top is 1.
            # [rbp+16] is 1. Correct.
            # So we must push in reverse list order?
            # args_to_push is [1, 2].
            # Reversed: [2, 1].
            # Push 2, Push 1. Correct.
            
            for arg in reversed(args_to_push):
                self._load_to_rax(arg)
                self._emit("    push rax")
                
            self._emit(f"    call {func_name}")
            
            # Cleanup Stack
            if num_args > 0:
                self._emit(f"    add rsp, {num_args * 8}")
                
            self._store_rax(instr.result)

        elif instr.opcode == OpCode.LOAD_PARAM:
            # LOAD_PARAM index (0-based)
            # Reads [rbp + 16 + index*8]
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
        offset = self.current_frame.get_offset(dest_var)
        self._emit(f"    mov [rbp - {offset}], {src_reg}")

    def _emit(self, line: str):
        self.output.append(line)

    def _emit_header(self):
        self.output.append("section .data")
        self.output.append('    fmt_int db "%d", 10, 0')
        self.output.append("")
        self.output.append("section .text")
        self.output.append("    extern printf")
        self.output.append("    extern scanf")
        self.output.append("")

    def _emit_footer(self):
        pass
