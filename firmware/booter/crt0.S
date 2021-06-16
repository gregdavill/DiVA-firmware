.global main
.global _start

_start:
crt_init:
  la sp, _fstack + 4
  j main