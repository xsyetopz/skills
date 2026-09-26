/* Null dereference two calls deep; lldb in batch mode prints the frames. */
#include <stddef.h>
#include <stdio.h>

struct config {
  const char *name;
};

static size_t name_length(const struct config *config) {
  size_t length = 0;
  while (config->name[length] != '\0') {
    length++;
  }
  return length;
}

static const struct config *load_config(int present) {
  static const struct config loaded = {"prod"};
  return present ? &loaded : NULL;
}

int main(int argc, char **argv) {
  (void)argv;
  const struct config *config = load_config(argc > 1);
  printf("%zu\n", name_length(config));
  return 0;
}
