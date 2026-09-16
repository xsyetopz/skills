#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

_Static_assert(CHAR_BIT == 8,
               "This byte-histogram fixture requires 8-bit bytes");

static void require(int condition, const char *message) {
  if (!condition) {
    fprintf(stderr, "%s\n", message);
    exit(EXIT_FAILURE);
  }
}
static void *allocate(size_t count, size_t width) {
  require(width != 0 && count <= SIZE_MAX / width, "allocation size overflow");
  void *result = calloc(count == 0 ? 1 : count, width);
  require(result != NULL, "allocation failed");
  return result;
}
static size_t joined_length(const char *const *parts, size_t count) {
  size_t total = 0;
  for (size_t i = 0; i < count; ++i) {
    size_t length = strlen(parts[i]);
    require(length < SIZE_MAX - total, "joined size overflow including NUL");
    total += length;
  }
  return total;
}
static char *baseline_join(const char *const *parts, size_t count) {
  char *out = allocate(joined_length(parts, count) + 1, 1);
  for (size_t i = 0; i < count; ++i)
    strcat(out, parts[i]);
  return out;
}
static char *candidate_join(const char *const *parts, size_t count) {
  char *out = allocate(joined_length(parts, count) + 1, 1);
  size_t offset = 0;
  for (size_t i = 0; i < count; ++i) {
    size_t length = strlen(parts[i]);
    memcpy(out + offset, parts[i], length);
    offset += length;
  }
  out[offset] = '\0';
  return out;
}
static void baseline_histogram(const unsigned char *bytes, size_t size,
                               size_t out[256]) {
  for (size_t value = 0; value < 256; ++value) {
    out[value] = 0;
    for (size_t i = 0; i < size; ++i)
      if (bytes[i] == value)
        ++out[value];
  }
}
static void candidate_histogram(const unsigned char *bytes, size_t size,
                                size_t out[256]) {
  for (size_t value = 0; value < 256; ++value)
    out[value] = 0;
  for (size_t i = 0; i < size; ++i)
    ++out[bytes[i]];
}
static uint64_t baseline_matrix(const uint64_t *values, size_t rows,
                                size_t columns) {
  uint64_t sum = 0;
  for (size_t column = 0; column < columns; ++column)
    for (size_t row = 0; row < rows; ++row)
      sum += values[row * columns + column];
  return sum;
}
static uint64_t candidate_matrix(const uint64_t *values, size_t rows,
                                 size_t columns) {
  uint64_t sum = 0;
  for (size_t row = 0; row < rows; ++row)
    for (size_t column = 0; column < columns; ++column)
      sum += values[row * columns + column];
  return sum;
}
struct filtered {
  uint32_t *values;
  size_t count;
};
static struct filtered baseline_filter(const uint32_t *values, size_t size) {
  struct filtered result = {allocate(size, sizeof(*values)), size};
  if (size != 0)
    memcpy(result.values, values, size * sizeof(*values));
  size_t i = 0;
  while (i < result.count) {
    if (result.values[i] == 0) {
      memmove(result.values + i, result.values + i + 1,
              (result.count - i - 1) * sizeof(*values));
      --result.count;
    } else
      ++i;
  }
  return result;
}
static struct filtered candidate_filter(const uint32_t *values, size_t size) {
  struct filtered result = {allocate(size, sizeof(*values)), 0};
  for (size_t i = 0; i < size; ++i)
    if (values[i] != 0)
      result.values[result.count++] = values[i];
  return result;
}
static void verify(void) {
  const char *parts[] = {"a", "", "\xc3\xa9", "\xf0\x9f\x99\x82"};
  char *a = baseline_join(parts, 4), *b = candidate_join(parts, 4);
  require(strcmp(a, "a\xc3\xa9\xf0\x9f\x99\x82") == 0 && strcmp(a, b) == 0,
          "join expected result");
  free(a);
  free(b);
  a = baseline_join(parts, 0);
  b = candidate_join(parts, 0);
  require(a[0] == '\0' && b[0] == '\0', "empty join");
  free(a);
  free(b);
  unsigned char all_bytes[256];
  size_t rh[256], gh[256];
  for (size_t i = 0; i < 256; ++i)
    all_bytes[i] = (unsigned char)i;
  baseline_histogram(all_bytes, 256, rh);
  candidate_histogram(all_bytes, 256, gh);
  for (size_t i = 0; i < 256; ++i)
    require(rh[i] == 1 && gh[i] == 1, "histogram expected result");
  baseline_histogram(all_bytes, 0, rh);
  candidate_histogram(all_bytes, 0, gh);
  for (size_t i = 0; i < 256; ++i)
    require(rh[i] == 0 && gh[i] == 0, "empty histogram");
  uint64_t matrix[] = {1, 2, 3, 4, 5, 6};
  require(baseline_matrix(matrix, 2, 3) == 21 &&
              candidate_matrix(matrix, 2, 3) == 21,
          "matrix expected result");
  uint64_t overflow[] = {UINT64_MAX, 1};
  require(baseline_matrix(overflow, 1, 2) == 0 &&
              candidate_matrix(overflow, 1, 2) == 0,
          "unsigned modular arithmetic");
  for (size_t length = 0; length <= 6; ++length) {
    size_t possibilities = 1;
    for (size_t i = 0; i < length; ++i)
      possibilities *= 3;
    for (size_t code = 0; code < possibilities; ++code) {
      uint32_t values[6] = {0};
      size_t rest = code;
      for (size_t i = 0; i < length; ++i) {
        values[i] = (uint32_t)(rest % 3);
        rest /= 3;
      }
      struct filtered baseline = baseline_filter(values, length),
                      candidate = candidate_filter(values, length);
      require(baseline.count == candidate.count, "filter length");
      require(memcmp(baseline.values, candidate.values,
                     baseline.count * sizeof(uint32_t)) == 0,
              "filter values");
      size_t expected = 0;
      for (size_t i = 0; i < length; ++i)
        if (values[i] != 0) {
          require(baseline.values[expected] == values[i],
                  "filter stable order");
          ++expected;
        }
      require(expected == baseline.count, "filter expected result");
      free(baseline.values);
      free(candidate.values);
    }
  }
  puts("PASS C17: four pairs, exhaustive filter and binary/expected result "
       "tests");
}
static size_t parse_size(const char *text) {
  require(text[0] != '-' && text[0] != '\0', "nonnegative integer required");
  char *end = NULL;
  errno = 0;
  unsigned long value = strtoul(text, &end, 10);
  require(errno == 0 && end != text && *end == '\0' && value <= 100000,
          "size 0..100000");
  return (size_t)value;
}
int main(int argc, char **argv) {
  if (argc == 2 && strcmp(argv[1], "verify") == 0) {
    verify();
    return EXIT_SUCCESS;
  }
  require(argc == 4, "usage: c-pairs verify | baseline|candidate CASE SIZE");
  int candidate = strcmp(argv[1], "candidate") == 0;
  require(candidate || strcmp(argv[1], "baseline") == 0, "bad variant");
  size_t which = parse_size(argv[2]), size = parse_size(argv[3]);
  if (which == 1) {
    const char **parts = allocate(size, sizeof(*parts));
    for (size_t i = 0; i < size; ++i)
      parts[i] = "ab";
    char *out =
        candidate ? candidate_join(parts, size) : baseline_join(parts, size);
    puts(out);
    free(out);
    free(parts);
  } else if (which == 2) {
    unsigned char *bytes = allocate(size, 1);
    for (size_t i = 0; i < size; ++i)
      bytes[i] = (unsigned char)(i % 256);
    size_t counts[256];
    if (candidate)
      candidate_histogram(bytes, size, counts);
    else
      baseline_histogram(bytes, size, counts);
    for (size_t i = 0; i < 256; ++i)
      printf("%zu%c", counts[i], i == 255 ? '\n' : ',');
    free(bytes);
  } else if (which == 3) {
    const size_t columns = 31;
    uint64_t *values = allocate(size * columns, sizeof(*values));
    for (size_t i = 0; i < size * columns; ++i)
      values[i] = i % 31;
    printf("%" PRIu64 "\n", candidate ? candidate_matrix(values, size, columns)
                                      : baseline_matrix(values, size, columns));
    free(values);
  } else if (which == 4) {
    uint32_t *values = allocate(size, sizeof(*values));
    for (size_t i = 0; i < size; ++i)
      values[i] = (uint32_t)(i % 3);
    struct filtered out = candidate ? candidate_filter(values, size)
                                    : baseline_filter(values, size);
    for (size_t i = 0; i < out.count; ++i)
      printf("%" PRIu32 ",", out.values[i]);
    putchar('\n');
    free(out.values);
    free(values);
  } else
    require(0, "case 1..4");
  return EXIT_SUCCESS;
}
