# Assembly: add two integer arguments

These are separate functions for four calling conventions. They return the sum
without accessing memory. Integer overflow wraps at the register width.

## x86-64, System V ABI, AT&T syntax

```asm
.text
.globl add_two
add_two:
    movq %rdi, %rax
    addq %rsi, %rax
    retq
```

## ARM Thumb, Cortex-M0

```asm
.syntax unified
.thumb
.text
.globl add_two
.thumb_func
add_two:
    adds r0, r0, r1
    bx lr
```

## AArch64

```asm
.text
.globl add_two
add_two:
    add x0, x0, x1
    ret
```

## MIPS32, o32 ABI

```asm
.set noreorder
.text
.globl add_two
add_two:
    addu $v0, $a0, $a1
    jr $ra
    nop
```

The last `nop` fills the MIPS branch delay slot. `addu` does not trap on signed
overflow. Register meanings and instruction availability depend on the ABI and
CPU; similar spellings across architectures are not interchangeable.

Inspect the encoding without executing the function:

```sh
nostromo-tool llvm-mc --triple=x86_64-unknown-freebsd --show-encoding example.s
nostromo-tool llvm-mc --triple=thumbv6m-none-eabi --show-encoding example.s
nostromo-tool llvm-mc --triple=aarch64-none-elf --show-encoding example.s
nostromo-tool llvm-mc --triple=mipsel-none-elf --show-encoding example.s
```

Use the command matching the source block. **DOCS → LLVM ASSEMBLER** explains the
assembler options. LLVM can validate and encode instructions; it is not a complete
vendor ISA manual. Keep the exact CPU's programming manual and board datasheet
locally when a project depends on registers, privilege levels or timing.
