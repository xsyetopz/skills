// Must NOT compile: consteval requires a constant argument.
// verify.sh (diagnose mode) expects this compile to fail.
#include <string_view>

consteval unsigned long key(std::string_view s) {
  unsigned long x = 14695981039346656037UL;
  for (char c : s) {
    x = (x ^ static_cast<unsigned char>(c)) * 1099511628211UL;
  }
  return x;
}

unsigned long runtime_key(std::string_view s) {
  return key(s); // error: s is not a constant expression
}
