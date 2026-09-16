#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_set>
#include <utility>
#include <vector>

using Values = std::vector<std::int64_t>;
static auto baseline_append(Values const &values) -> Values {
  auto result = Values{};
  for (auto const value : values) {
    auto next = Values{result};
    next.push_back(value);
    result = std::move(next);
  }
  return result;
}
static auto candidate_append(Values const &values) -> Values {
  auto result = Values{};
  result.reserve(values.size());
  for (auto const value : values)
    result.push_back(value);
  return result;
}
static auto baseline_fields(std::string const &text)
    -> std::vector<std::size_t> {
  auto result = std::vector<std::size_t>{};
  auto start = std::size_t{0};
  while (true) {
    auto const end = text.find(':', start);
    auto const count =
        end == std::string::npos ? text.size() - start : end - start;
    auto const field = text.substr(start, count);
    result.push_back(field.size());
    if (end == std::string::npos)
      break;
    start = end + 1;
  }
  return result;
}
static auto candidate_fields(std::string const &owner)
    -> std::vector<std::size_t> {
  auto const text = std::string_view{owner};
  auto result = std::vector<std::size_t>{};
  auto start = std::size_t{0};
  while (true) {
    auto const end = text.find(':', start);
    auto const count =
        end == std::string_view::npos ? text.size() - start : end - start;
    auto const field = text.substr(start, count);
    result.push_back(field.size());
    if (end == std::string_view::npos)
      break;
    start = end + 1;
  }
  return result; // No view escapes; returned lengths own their storage.
}
static auto baseline_filter(Values const &values) -> Values {
  auto result = Values{values};
  for (auto it = result.begin(); it != result.end();) {
    if (*it == 0)
      it = result.erase(it);
    else
      ++it;
  }
  return result;
}
static auto candidate_filter(Values const &values) -> Values {
  auto result = Values{values};
  result.erase(std::remove(result.begin(), result.end(), 0), result.end());
  return result;
}
static auto baseline_membership(Values const &values, Values const &queries)
    -> std::vector<bool> {
  auto result = std::vector<bool>{};
  for (auto const query : queries)
    result.push_back(std::find(values.begin(), values.end(), query) !=
                     values.end());
  return result;
}
static auto candidate_membership(Values const &values, Values const &queries)
    -> std::vector<bool> {
  auto const members =
      std::unordered_set<std::int64_t>{values.begin(), values.end()};
  auto result = std::vector<bool>{};
  for (auto const query : queries)
    result.push_back(members.find(query) != members.end());
  return result;
}
struct Record {
  double x;
  double y;
};
struct Records {
  std::vector<double> x;
  std::vector<double> y;
};
static auto baseline_aos_x_sum(Values const &values) -> double {
  auto records = std::vector<Record>{};
  records.reserve(values.size());
  for (auto const value : values)
    records.push_back({static_cast<double>(value), 1.0});
  auto sum = 0.0;
  for (auto const &record : records)
    sum += record.x;
  return sum;
}
static auto candidate_soa_x_sum(Values const &values) -> double {
  auto records = Records{};
  records.x.reserve(values.size());
  records.y.reserve(values.size());
  for (auto const value : values) {
    records.x.push_back(static_cast<double>(value));
    records.y.push_back(1.0);
  }
  auto sum = 0.0;
  for (auto const value : records.x)
    sum += value;
  return sum;
}
class Operation {
public:
  virtual ~Operation() = default;
  virtual auto apply(std::int64_t value) const -> std::int64_t = 0;
};
class AddOne final : public Operation {
public:
  auto apply(std::int64_t const value) const -> std::int64_t override {
    return value + 1;
  }
};
static auto baseline_polymorphic(Values const &values) -> std::int64_t {
  auto operations = std::vector<std::unique_ptr<Operation>>{};
  operations.reserve(values.size());
  for (auto const ignored : values) {
    static_cast<void>(ignored);
    operations.push_back(std::make_unique<AddOne>());
  }
  auto sum = std::int64_t{0};
  for (auto i = std::size_t{0}; i < values.size(); ++i)
    sum += operations[i]->apply(values[i]);
  return sum;
}
static auto candidate_contiguous(Values const &values) -> std::int64_t {
  auto sum = std::int64_t{0};
  for (auto const value : values)
    sum += value + 1;
  return sum;
}
static auto require(bool const condition, char const *const message) -> void {
  if (!condition)
    throw std::runtime_error(message);
}
static auto verify() -> void {
  for (auto length = std::size_t{0}; length <= 6; ++length) {
    auto possibilities = std::size_t{1};
    for (auto i = std::size_t{0}; i < length; ++i)
      possibilities *= 3;
    for (auto code = std::size_t{0}; code < possibilities; ++code) {
      auto values = Values{};
      auto rest = code;
      for (std::size_t i = 0; i < length; ++i) {
        values.push_back(static_cast<std::int64_t>(rest % 3) - 1);
        rest /= 3;
      }
      auto const saved = values;
      require(baseline_append(values) == values &&
                  candidate_append(values) == values,
              "append expected result");
      require(baseline_filter(values) == candidate_filter(values),
              "filter equivalent");
      auto expected = Values{};
      for (auto const value : values)
        if (value != 0)
          expected.push_back(value);
      require(baseline_filter(values) == expected,
              "filter stable expected result");
      require(baseline_membership(values, {0, 9}) ==
                  candidate_membership(values, {0, 9}),
              "membership equivalent");
      require(baseline_aos_x_sum(values) == candidate_soa_x_sum(values),
              "AoS and SoA checksum equivalent");
      require(baseline_polymorphic(values) == candidate_contiguous(values),
              "polymorphic and contiguous traversal equivalent");
      require(values == saved, "input mutated");
    }
  }
  auto const expected = std::vector<std::size_t>{0, 2, 0, 4, 0};
  auto const unicode = std::string{":\xc3\xa9::\xf0\x9f\x99\x82:"};
  require(baseline_fields(unicode) == expected &&
              candidate_fields(unicode) == expected,
          "UTF8 byte lengths");
  require(baseline_fields("") == std::vector<std::size_t>{0}, "empty field");
  require(candidate_fields("") == std::vector<std::size_t>{0},
          "empty view field");
  auto const binary = std::string{"a\0:b", 4};
  require(baseline_fields(binary) == std::vector<std::size_t>({2, 1}),
          "embedded NUL");
  require(candidate_fields(binary) == baseline_fields(binary), "NUL view");
  auto const boundary = Values{std::numeric_limits<std::int64_t>::min(),
                               std::numeric_limits<std::int64_t>::max()};
  require(baseline_append(boundary) == boundary &&
              candidate_append(boundary) == boundary,
          "boundary values");
  require(baseline_membership({2, 2}, {2, 3}) ==
              std::vector<bool>({true, false}),
          "membership expected result");
  require(candidate_membership({2, 2}, {2, 3}) ==
              std::vector<bool>({true, false}),
          "set expected result");
  auto capacity_only = Values{};
  capacity_only.reserve(8);
  require(capacity_only.empty(), "reserve must not become resize");
  std::cout << "PASS C++17: four pairs, exhaustive and ownership/expected "
               "result tests\n";
}
static auto parse_size(std::string const &text) -> std::size_t {
  require(!text.empty() && text[0] != '-', "nonnegative integer required");
  auto end = std::size_t{0};
  auto const number = std::stoull(text, &end, 10);
  require(end == text.size() && number <= 100000, "size 0..100000");
  return static_cast<std::size_t>(number);
}
template <class T> static auto print(std::vector<T> const &values) -> void {
  for (auto const value : values)
    std::cout << value << ',';
  std::cout << '\n';
}
auto main(int const argc, char **const argv) -> int {
  try {
    if (argc == 2 && std::string(argv[1]) == "verify") {
      verify();
      return 0;
    }
    require(argc == 4,
            "usage: cpp-pairs verify | baseline|candidate CASE SIZE");
    auto const variant = std::string{argv[1]};
    require(variant == "baseline" || variant == "candidate", "bad variant");
    auto const candidate = variant == "candidate";
    auto const which = parse_size(argv[2]);
    auto const size = parse_size(argv[3]);
    auto values = Values{};
    for (auto i = std::size_t{0}; i < size; ++i)
      values.push_back(static_cast<std::int64_t>(i % 31) - 15);
    switch (which) {
    case 1:
      print(candidate ? candidate_append(values) : baseline_append(values));
      break;
    case 2: {
      auto text = std::string{};
      for (auto i = std::size_t{0}; i < size; ++i)
        text += "abcd:";
      print(candidate ? candidate_fields(text) : baseline_fields(text));
      break;
    }
    case 3:
      print(candidate ? candidate_filter(values) : baseline_filter(values));
      break;
    case 4:
      print(candidate ? candidate_membership(values, values)
                      : baseline_membership(values, values));
      break;
    case 5:
      std::cout << (candidate ? candidate_soa_x_sum(values)
                              : baseline_aos_x_sum(values))
                << '\n';
      break;
    case 6:
      std::cout << (candidate ? candidate_contiguous(values)
                              : baseline_polymorphic(values))
                << '\n';
      break;
    default:
      throw std::invalid_argument("case 1..6");
    }
  } catch (std::exception const &error) {
    std::cerr << error.what() << '\n';
    return 1; // Deliberate CLI error boundary, never swallow.
  }
  return 0;
}
