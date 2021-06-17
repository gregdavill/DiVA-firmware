.global main
.global _start

/* 
  Very simple crt0. We don't care about interrupts,bss,data regions. 
  Just set the stack pointer and hop over to main.
*/

_start:
crt_init:
  la sp, _fstack + 4
  j main