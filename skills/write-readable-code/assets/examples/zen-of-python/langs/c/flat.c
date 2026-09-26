/* Flat is better than nested: guard clauses return early, and the one
 * success path sits at the function's top level. */
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

enum status { SHIP, HOLD_UNPAID, HOLD_EMPTY, HOLD_NO_ADDRESS };

struct order {
  bool paid;
  int items;
  const char *address; /* NULL when missing */
};

static enum status decide_nested(const struct order *o) {
  if (o->paid) {
    if (o->items > 0) {
      if (o->address != NULL) {
        return SHIP;
      } else {
        return HOLD_NO_ADDRESS;
      }
    } else {
      return HOLD_EMPTY;
    }
  } else {
    return HOLD_UNPAID;
  }
}

static enum status decide(const struct order *o) {
  if (!o->paid) {
    return HOLD_UNPAID;
  }
  if (o->items <= 0) {
    return HOLD_EMPTY;
  }
  if (o->address == NULL) {
    return HOLD_NO_ADDRESS;
  }
  return SHIP;
}

int main(void) {
  const int item_counts[] = {0, 1, 3};
  const char *addresses[] = {NULL, "Main St 1"};
  int cases = 0;
  for (int paid = 0; paid <= 1; paid++) {
    for (size_t i = 0; i < 3; i++) {
      for (size_t a = 0; a < 2; a++) {
        struct order o = {paid != 0, item_counts[i], addresses[a]};
        if (decide(&o) != decide_nested(&o)) {
          printf("FAIL paid=%d items=%d\n", paid, item_counts[i]);
          return 1;
        }
        cases++;
      }
    }
  }
  printf("flat: %d cases match the nested version\n", cases);
  return 0;
}
