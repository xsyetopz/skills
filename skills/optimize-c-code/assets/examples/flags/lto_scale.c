/* Separate translation unit: without LTO the compiler of lto_main.c
 * cannot see this body, so every call stays a call. */
int lto_scale(int x);

int lto_scale(int x) { return x * 3 + 1; }
