# This translates intermediate operations specifically into RISC-V native assembly.

from typing import List
from src.ir.instructions import Instruction, OpCode
from src.backend.common.stack_frame import StackFrame


class RISCVGenerator:


    def __init__(self):
        # This initializes the base properties.
        self.output: List[str] = []
        self.current_frame = None
        self._pending_params = []
        self._current_func_name = None
        self._frame_locals_size = 0
        self.strings = []

    def generate(self, instructions: List[Instruction]) -> str:
        # This takes the parsed data and spits out the actual generated implementation.
        self.strings = []
        for instr in instructions:
            if instr.opcode == OpCode.LOAD_STR:
                if instr.arg1 not in self.strings:
                    self.strings.append(instr.arg1)

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

        self._emit_footer()
        return "\n".join(self.output)

    def _compile_function(self, instrs: List[Instruction]):
        # This handles the primary logic for compile function operations.
        func_name = instrs[0].arg1
        self._current_func_name = func_name

                          
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

                                                                  
        locals_size = frame.total_size
        locals_size = (locals_size + 15) & ~15             
        if locals_size == 0:
            locals_size = 16                                                            

        self._frame_locals_size = locals_size
        frame_size = locals_size + 16                                    

                          
        self._emit(f"# --- Function {func_name} ---")
        self._emit(f".globl {func_name}")
        self._emit(f"{func_name}:")
        self._emit(f"    addi sp, sp, -{frame_size}")
        self._emit(f"    sd   ra, {locals_size + 8}(sp)")                    
        self._emit(f"    sd   s0, {locals_size}(sp)")                         
        self._emit(f"    addi s0, sp, {locals_size}")                             

                      
        for instr in instrs[1:-1]:
            self._emit_instruction(instr)

                                                     
        self._emit(f".exit_{func_name}:")
        self._emit(f"    ld   ra, {locals_size + 8}(sp)")
        self._emit(f"    ld   s0, {locals_size}(sp)")
        self._emit(f"    addi sp, sp, {frame_size}")
        self._emit("    ret")

    def _emit_instruction(self, instr: Instruction):
        # This handles the primary logic for emit instruction operations.
        self._emit(f"    # {instr}")

        if instr.opcode == OpCode.MOV:
            self._load_to_t0(instr.arg1)
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.ADD:
            self._load_to_t0(instr.arg1)
            self._emit("    mv   t1, t0")
            self._load_to_t0(instr.arg2)
            self._emit("    add  t0, t1, t0")
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.SUB:
            self._load_to_t0(instr.arg1)
            self._emit("    mv   t1, t0")
            self._load_to_t0(instr.arg2)
            self._emit("    sub  t0, t1, t0")
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.MUL:
            self._load_to_t0(instr.arg1)
            self._emit("    mv   t1, t0")
            self._load_to_t0(instr.arg2)
            self._emit("    mul  t0, t1, t0")
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.DIV:
            self._load_to_t0(instr.arg1)
            self._emit("    mv   t1, t0")
            self._load_to_t0(instr.arg2)
            self._emit("    div  t0, t1, t0")
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.MOD:
            self._load_to_t0(instr.arg1)
            self._emit("    mv   t1, t0")
            self._load_to_t0(instr.arg2)
            self._emit("    rem  t0, t1, t0")
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.LSHIFT:
            count = instr.arg2
            self._load_to_t0(instr.arg1)
            if isinstance(count, int):
                self._emit(f"    slli t0, t0, {count}")
            else:
                self._emit("    mv   t1, t0")
                self._load_to_t0(count)
                self._emit("    sll  t0, t1, t0")
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.RSHIFT:
            count = instr.arg2
            self._load_to_t0(instr.arg1)
            if isinstance(count, int):
                self._emit(f"    srai t0, t0, {count}")
            else:
                self._emit("    mv   t1, t0")
                self._load_to_t0(count)
                self._emit("    sra  t0, t1, t0")
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.LT:
                                
            self._load_to_t0(instr.arg1)
            self._emit("    mv   t1, t0")
            self._load_to_t0(instr.arg2)
            self._emit("    slt  t0, t1, t0")
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.GT:
                                                    
            self._load_to_t0(instr.arg1)
            self._emit("    mv   t1, t0")
            self._load_to_t0(instr.arg2)
            self._emit("    slt  t0, t0, t1")                  
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.EQ:
                                                         
            self._load_to_t0(instr.arg1)
            self._emit("    mv   t1, t0")
            self._load_to_t0(instr.arg2)
            self._emit("    sub  t0, t1, t0")
            self._emit("    seqz t0, t0")
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.NEQ:
                                                         
            self._load_to_t0(instr.arg1)
            self._emit("    mv   t1, t0")
            self._load_to_t0(instr.arg2)
            self._emit("    sub  t0, t1, t0")
            self._emit("    snez t0, t0")
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.LTE:
                                   
            self._load_to_t0(instr.arg1)
            self._emit("    mv   t1, t0")
            self._load_to_t0(instr.arg2)
            self._emit("    slt  t0, t0, t1")                  
            self._emit("    xori t0, t0, 1")                     
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.GTE:
                                   
            self._load_to_t0(instr.arg1)
            self._emit("    mv   t1, t0")
            self._load_to_t0(instr.arg2)
            self._emit("    slt  t0, t1, t0")                  
            self._emit("    xori t0, t0, 1")                     
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.PRINT:
                                  
                                      
            self._load_to_t0(instr.arg1)
            self._emit("    mv   a1, t0")
            self._emit("    la   a0, fmt_int")
            self._emit("    call printf")

        elif instr.opcode == OpCode.PRINT_STR:
            self._load_to_t0(instr.arg1)
            self._emit("    mv   a1, t0")
            self._emit("    la   a0, fmt_str")
            self._emit("    call printf")

        elif instr.opcode == OpCode.LOAD_STR:
            idx = self.strings.index(instr.arg1)
            self._emit(f"    la   t0, str_{idx}")
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.RETURN:
            if instr.arg1 is not None:
                self._load_to_t0(instr.arg1)
                self._emit("    mv   a0, t0")
            self._emit(f"    j    .exit_{self._current_func_name}")

        elif instr.opcode == OpCode.LABEL:
            self._emit(f"{instr.arg1}:")

        elif instr.opcode == OpCode.JMP:
            self._emit(f"    j    {instr.arg1}")

        elif instr.opcode == OpCode.JMP_IF_FALSE:
            self._load_to_t0(instr.arg1)
            self._emit(f"    beqz t0, {instr.arg2}")

                        
        elif instr.opcode == OpCode.ARR_DECL:
            pass                             

        elif instr.opcode == OpCode.ALOAD:
            self._load_to_t0(instr.arg2)                        
            self._emit("    slli t0, t0, 3")                         

            arr_base = self.current_frame.get_offset(instr.arg1)
            if self.current_frame.is_reference(instr.arg1):
                self._emit(f"    ld   t1, -{arr_base}(s0)")                 
            else:
                self._emit(f"    addi t1, s0, -{arr_base}")                  

            self._emit("    add  t1, t1, t0")                              
            self._emit("    ld   t0, 0(t1)")                              
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.ASTORE:
            self._load_to_t0(instr.arg2)                         
            self._emit("    slli t0, t0, 3")                          

            arr_base = self.current_frame.get_offset(instr.arg1)
            if self.current_frame.is_reference(instr.arg1):
                self._emit(f"    ld   t1, -{arr_base}(s0)")
            else:
                self._emit(f"    addi t1, s0, -{arr_base}")

            self._emit("    add  t1, t1, t0")                               
            self._emit("    mv   t2, t1")                                  

            self._load_to_t0(instr.result)                                  
            self._emit("    sd   t0, 0(t2)")

                           
        elif instr.opcode == OpCode.PARAM:
            self._pending_params.append((instr.arg1, False))

        elif instr.opcode == OpCode.PARAM_REF:
            self._pending_params.append((instr.arg1, True))

        elif instr.opcode == OpCode.CALL:
            func_name = instr.arg1
            num_args  = instr.arg2

            args_to_push = self._pending_params[-num_args:]
            self._pending_params = self._pending_params[:-num_args]

                                                              
            for arg, is_ref in reversed(args_to_push):
                if is_ref:
                    arr_base = self.current_frame.get_offset(arg)
                    if self.current_frame.is_reference(arg):
                        self._emit(f"    ld   t0, -{arr_base}(s0)")
                    else:
                        self._emit(f"    addi t0, s0, -{arr_base}")
                else:
                    self._load_to_t0(arg)
                self._emit("    addi sp, sp, -8")
                self._emit("    sd   t0, 0(sp)")

            self._emit(f"    call {func_name}")

                          
            if num_args > 0:
                self._emit(f"    addi sp, sp, {num_args * 8}")

                                   
            if instr.result:
                self._emit("    mv   t0, a0")
                self._store_t0(instr.result)

        elif instr.opcode == OpCode.LOAD_PARAM:
                                                                       
                                                           
                                   
                                                           
            idx = instr.arg1
            offset = 16 + idx * 8
            self._emit(f"    ld   t0, {offset}(s0)")
            self._store_t0(instr.result)

        elif instr.opcode == OpCode.LOAD_PARAM_REF:
            idx = instr.arg1
            offset = 16 + idx * 8
            self._emit(f"    ld   t0, {offset}(s0)")
            self._store_t0(instr.result)

    def _load_to_t0(self, arg):
                                                                
        # This handles the primary logic for load to t0 operations.
        if isinstance(arg, int):
            self._emit(f"    li   t0, {arg}")
        elif isinstance(arg, str):
            offset = self.current_frame.get_offset(arg)
            self._emit(f"    ld   t0, -{offset}(s0)")
        else:
            raise Exception(f"RISCVGen: Unknown arg type: {type(arg)} = {arg}")

    def _store_t0(self, dest_var, src_reg="t0"):
                                                            
        # This handles the primary logic for store t0 operations.
        if dest_var is None:
            return
        offset = self.current_frame.get_offset(dest_var)
        self._emit(f"    sd   {src_reg}, -{offset}(s0)")

    def _emit(self, line: str):
        # This handles the primary logic for emit operations.
        self.output.append(line)

    def _emit_header(self):
        # This handles the primary logic for emit header operations.
        self.output.append(".section .data")
        self.output.append('fmt_int: .string "%ld\\n"')
        self.output.append('fmt_str: .string "%s"')
        self.output.append('fmt_read_int: .string "%ld"')
        for i, s in enumerate(self.strings):
            self.output.append(f'str_{i}: .string "{s}"')
        self.output.append("")
        self.output.append(".section .text")
        self.output.append(".globl readInt")
        self.output.append("readInt:")
        self.output.append("    addi sp, sp, -32")
        self.output.append("    sd   ra, 24(sp)")
        self.output.append("    sd   s0, 16(sp)")
        self.output.append("    addi s0, sp, 32")
        self.output.append("    la   a0, fmt_read_int")
        self.output.append("    addi a1, s0, -24")
        self.output.append("    call scanf")
        self.output.append("    ld   a0, -24(s0)")
        self.output.append("    ld   ra, 24(sp)")
        self.output.append("    ld   s0, 16(sp)")
        self.output.append("    addi sp, sp, 32")
        self.output.append("    ret")
        self.output.append("")

    def _emit_footer(self):
        # This handles the primary logic for emit footer operations.
        self._emit("")                                                                       