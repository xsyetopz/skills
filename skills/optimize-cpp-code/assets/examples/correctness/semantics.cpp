// Identical oracles for a deliberate mutant and its correction. No undefined behavior.
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <limits>
#include <string>
#include <string_view>
#include <vector>

static bool contract(bool bad, int topic) {
  switch (topic) {
  case 1: { // Refuse an increment whose mathematical result is not representable.
    auto accepts = [bad](int x) { return bad || x < std::numeric_limits<int>::max(); };
    return !accepts(std::numeric_limits<int>::max()) && accepts(4);
  }
  case 2: { // IEEE-754 binary32 bit representation, not numeric conversion.
    static_assert(sizeof(float) == sizeof(std::uint32_t) && std::numeric_limits<float>::is_iec559,
                  "This fixture requires IEEE-754 binary32");
    float value = 1.5F;
    std::uint32_t bits = 0;
    if (bad) bits = static_cast<std::uint32_t>(value);
    else std::memcpy(&bits, &value, sizeof bits);
    return bits == UINT32_C(0x3fc00000);
  }
  case 3: { // Overlapping copy. The mutant is a defined forward loop, not UB memcpy.
    char bytes[] = "abcd";
    if (bad) for (int i = 0; i < 3; ++i) bytes[i + 1] = bytes[i];
    else std::memmove(bytes + 1, bytes, 3);
    return std::string(bytes, 4) == "aabc";
  }
  case 4: { // Logical identity is not a position when preceding elements are inserted.
    std::vector<int> ids{11, 22};
    const auto old_index = std::size_t{1};
    const int saved_id = ids[old_index];
    ids.insert(ids.begin(), 7);
    int result = bad ? ids[old_index] : *std::find(ids.begin(), ids.end(), saved_id);
    return result == 22;
  }
  case 5: { // Snapshot vs borrowed view: owner stays alive in both variants.
    std::string owner = "before";
    const std::string copy = owner;
    const std::string_view view = owner;
    owner[0] = 'a';
    return (bad ? std::string(view) : copy) == "before";
  }
  case 6: { // Adjacent matches must all be erased.
    std::vector<int> values{1, 2, 2, 3};
    if (bad) {
      for (std::size_t i = 0; i < values.size(); ++i)
        if (values[i] == 2) values.erase(values.begin() + static_cast<std::ptrdiff_t>(i));
    } else values.erase(std::remove(values.begin(), values.end(), 2), values.end());
    return values == std::vector<int>({1, 3});
  }
  case 7: { // A deterministic legal interleaving: atomic load+store is not atomic RMW.
    std::atomic<int> count{0};
    if (bad) {
      int a = count.load(), b = count.load();
      count.store(a + 1); count.store(b + 1);
    } else { count.fetch_add(1); count.fetch_add(1); }
    return count.load() == 2;
  }
  case 8: { // A sign-preserving operation must distinguish negative zero.
    auto negative = [bad](double x) { return bad ? x < 0 : std::signbit(x); };
    return negative(-0.0) && !negative(0.0);
  }
  default: throw std::invalid_argument("topic must be 1..8");
  }
}
int main(int argc, char** argv) {
  try {
    if (argc != 3 || (std::string(argv[1]) != "red" && std::string(argv[1]) != "green"))
      throw std::invalid_argument("usage: red|green TOPIC");
    int topic = std::stoi(argv[2]);
    bool pass = contract(std::string(argv[1]) == "red", topic);
    std::cout << "CONTRACT topic " << topic << ": " << (pass ? "PASS" : "FAIL") << '\n';
    return pass ? 0 : 1;
  } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 2; }
}
