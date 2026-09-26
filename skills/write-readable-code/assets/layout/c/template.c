#include "component.h" /* own header first proves it is self-contained */

#include <stddef.h>
#include <stdint.h>

#define LOCAL_MACRO 1

static const size_t LOCAL_CONSTANT = 64;

struct private_state {
  size_t value;
};

static void private_helper(struct private_state *state);

void component_public_function(void) {
  struct private_state state = {LOCAL_CONSTANT * LOCAL_MACRO};
  private_helper(&state);
}

static void private_helper(struct private_state *state) {
  state->value += COMPONENT_PUBLIC_CONSTANT;
}
