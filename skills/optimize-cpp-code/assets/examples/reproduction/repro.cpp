#include <iostream>
#include <vector>

auto main() -> int {
  auto values = std::vector<int>{};
  values.reserve(1);
  values.push_back(1);

  auto const *const saved = values.data();
  values.push_back(2);
  std::cout << "actual pointer changed=" << std::boolalpha
            << (saved != values.data()) << "\nexpected stable handle\n";
  return saved != values.data() ? 0 : 1;
}
