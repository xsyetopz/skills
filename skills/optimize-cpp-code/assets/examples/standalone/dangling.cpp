// A string_view that outlives its std::string. verify.sh (sanitize mode)
// expects AddressSanitizer to report heap-use-after-free here.
#include <cstdio>
#include <string>
#include <string_view>

__attribute__((noinline)) std::string make_key(int i) {
  return "customer-account-identifier-" + std::to_string(i);
}

int main() {
  // The temporary std::string dies at the end of this full-expression.
  std::string_view const key = make_key(7);
  std::printf("%c\n", key[0]); // reads freed heap memory
  return 0;
}
