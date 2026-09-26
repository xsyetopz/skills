/* Off-by-one: copies len + 1 bytes into a len-byte buffer. */
#include <stdlib.h>
#include <string.h>

int main(void) {
  const char *source = "hello";
  size_t len = strlen(source);
  char *copy = malloc(len);
  memcpy(copy, source, len + 1); /* writes the terminator out of bounds */
  int first = copy[0];
  free(copy);
  return first == 'h' ? 0 : 2;
}
