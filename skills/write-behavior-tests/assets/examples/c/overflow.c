/* Off-by-one write that plain runs usually survive; ASan reports it. */
#include <stdio.h>
#include <stdlib.h>

static void fill(int *values, int count) {
  for (int i = 0; i <= count; i++) { /* bug: <= writes values[count] */
    values[i] = i;
  }
}

int main(void) {
  int *values = malloc(8 * sizeof *values);
  if (values == NULL) {
    return 2;
  }
  fill(values, 8);
  printf("sum of first two: %d\n", values[0] + values[1]);
  free(values);
  return 0;
}
