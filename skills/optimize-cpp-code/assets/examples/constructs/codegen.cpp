// Dispatch, compile-time evaluation, exceptions, and algorithms:
// references/codegen.md
#include "harness.hpp"

#include <algorithm>
#include <array>
#include <charconv>
#include <cstdint>
#include <cstdio>
#include <expected>
#include <functional>
#include <memory>
#include <ranges>
#include <stdexcept>
#include <string>
#include <string_view>
#include <system_error>
#include <variant>
#include <vector>

// --- Virtual dispatch and its replacements ------------------------------
struct Shape {
  virtual ~Shape() = default;
  virtual long area() const = 0;
};
struct Square : Shape {
  long side;
  explicit Square(long s) : side(s) {}
  long area() const override { return side * side; }
};
struct Rect : Shape {
  long w;
  long hgt;
  Rect(long a, long b) : w(a), hgt(b) {}
  long area() const override { return w * hgt; }
};
// final: no further override can exist, so a call through FinalSquare&
// has exactly one target.
struct FinalSquare final : Shape {
  long side;
  explicit FinalSquare(long s) : side(s) {}
  long area() const override { return side * side; }
};

// Plain value types for the static alternatives.
struct VSquare {
  long side;
  long area() const { return side * side; }
};
struct VRect {
  long w;
  long hgt;
  long area() const { return w * hgt; }
};
using AnyShape = std::variant<VSquare, VRect>;

// CRTP: the base calls the derived implementation without a vtable.
template <class D> struct ShapeBase {
  long area() const { return static_cast<D const *>(this)->area_impl(); }
};
struct CSquare : ShapeBase<CSquare> {
  long side;
  explicit CSquare(long s) : side(s) {}
  long area_impl() const { return side * side; }
};
template <class D> long crtp_total_impl(std::vector<D> const &v) {
  long s = 0;
  for (auto const &x : v) {
    s += x.area();
  }
  return s;
}
template <class T> long template_total_impl(std::vector<T> const &v) {
  long s = 0;
  for (auto const &x : v) {
    s += x.area();
  }
  return s;
}

extern "C" {
__attribute__((noinline)) long
virtual_total_baseline(std::vector<std::unique_ptr<Shape>> const &v) {
  long s = 0;
  for (auto const &p : v) {
    s += p->area(); // load vtable, indirect call
  }
  return s;
}
__attribute__((noinline)) long
template_total_candidate(std::vector<VSquare> const &v) {
  return template_total_impl(v);
}
__attribute__((noinline)) long
crtp_total_candidate(std::vector<CSquare> const &v) {
  return crtp_total_impl(v);
}
__attribute__((noinline)) long
variant_total_candidate(std::vector<AnyShape> const &v) {
  long s = 0;
  for (auto const &x : v) {
    s += std::visit([](auto const &shape) { return shape.area(); }, x);
  }
  return s;
}
__attribute__((noinline)) long
variant_index_candidate(std::vector<AnyShape> const &v) {
  long s = 0;
  for (auto const &x : v) {
    if (auto const *sq = std::get_if<VSquare>(&x)) {
      s += sq->area();
    } else {
      s += std::get<VRect>(x).area();
    }
  }
  return s;
}
__attribute__((noinline)) long nonfinal_area_baseline(Square const &s) {
  return s.area(); // Square may be further derived: indirect call
}
__attribute__((noinline)) long final_area_candidate(FinalSquare const &s) {
  return s.area(); // devirtualized: FinalSquare::area is the only target
}

// --- std::function vs a template parameter ------------------------------
__attribute__((noinline)) long
apply_function_baseline(std::vector<long> const &v,
                        std::function<long(long)> const &f) {
  long s = 0;
  for (auto x : v) {
    s += f(x); // type-erased: indirect call per element
  }
  return s;
}
}

template <class F>
__attribute__((noinline)) long apply_template(std::vector<long> const &v,
                                              F const &f) {
  long s = 0;
  for (auto x : v) {
    s += f(x); // inlined: the callable's type is known
  }
  return s;
}
extern "C" __attribute__((noinline)) long
apply_template_candidate(std::vector<long> const &v, long k) {
  return apply_template(v, [k](long x) { return x * k + 1; });
}

// --- constexpr tables and consteval -------------------------------------
namespace {
constexpr std::array<std::uint32_t, 256> make_crc_table() {
  std::array<std::uint32_t, 256> t{};
  for (std::uint32_t i = 0; i < 256; ++i) {
    std::uint32_t c = i;
    for (int k = 0; k < 8; ++k) {
      c = (c & 1U) != 0 ? 0xEDB88320U ^ (c >> 1) : c >> 1;
    }
    t[i] = c;
  }
  return t;
}
std::array<std::uint32_t, 256> make_crc_table_runtime() {
  return make_crc_table();
}
} // namespace

extern "C" {
__attribute__((noinline)) std::uint32_t crc_static_baseline(char const *p,
                                                            std::size_t n) {
  // Dynamic initialization: a thread-safe guard is checked on every call.
  static std::array<std::uint32_t, 256> const table = make_crc_table_runtime();
  std::uint32_t c = 0xFFFFFFFFU;
  for (std::size_t i = 0; i < n; ++i) {
    c = table[(c ^ static_cast<unsigned char>(p[i])) & 0xFFU] ^ (c >> 8);
  }
  return c ^ 0xFFFFFFFFU;
}
__attribute__((noinline)) std::uint32_t crc_constexpr_candidate(char const *p,
                                                                std::size_t n) {
  // Constant initialization: the table is data in the binary; no guard.
  static constexpr auto table = make_crc_table();
  std::uint32_t c = 0xFFFFFFFFU;
  for (std::size_t i = 0; i < n; ++i) {
    c = table[(c ^ static_cast<unsigned char>(p[i])) & 0xFFU] ^ (c >> 8);
  }
  return c ^ 0xFFFFFFFFU;
}
}

namespace {
constexpr std::uint64_t fnv1a(std::string_view s) {
  std::uint64_t x = 14695981039346656037ULL;
  for (char ch : s) {
    x = (x ^ static_cast<unsigned char>(ch)) * 1099511628211ULL;
  }
  return x;
}
// consteval: every call must be a constant expression; a runtime argument
// is a compile error rather than a silent runtime hash.
consteval std::uint64_t key(std::string_view s) { return fnv1a(s); }
} // namespace

extern "C" {
__attribute__((noinline)) int route_runtime_baseline(char const *p,
                                                     std::size_t n) {
  auto const h = fnv1a({p, n});
  if (h == fnv1a("GET")) { // may be folded; not guaranteed
    return 1;
  }
  if (h == fnv1a("POST")) {
    return 2;
  }
  return 0;
}
__attribute__((noinline)) int route_consteval_candidate(char const *p,
                                                        std::size_t n) {
  switch (fnv1a({p, n})) {
  case key("GET"): // case labels require constants; key() guarantees it
    return 1;
  case key("POST"):
    return 2;
  default:
    return 0;
  }
}

// --- [[likely]] / [[unlikely]] ------------------------------------------
__attribute__((noinline)) long clamp_sum_baseline(long const *v,
                                                  std::size_t n) {
  long s = 0;
  for (std::size_t i = 0; i < n; ++i) {
    if (v[i] < 0) {
      s -= v[i] * 3;
    } else {
      s += v[i];
    }
  }
  return s;
}
__attribute__((noinline)) long clamp_sum_candidate(long const *v,
                                                   std::size_t n) {
  long s = 0;
  for (std::size_t i = 0; i < n; ++i) {
    if (v[i] < 0) [[unlikely]] {
      s -= v[i] * 3;
    } else {
      s += v[i];
    }
  }
  return s;
}
}

// --- Exceptions vs std::expected ----------------------------------------
namespace {
__attribute__((noinline)) int parse_throw(std::string_view s) {
  int v = 0;
  auto const [p, ec] = std::from_chars(s.data(), s.data() + s.size(), v);
  if (ec != std::errc{} || p != s.data() + s.size()) {
    throw std::invalid_argument("not an int");
  }
  return v;
}
__attribute__((noinline)) std::expected<int, std::errc>
parse_expected(std::string_view s) {
  int v = 0;
  auto const [p, ec] = std::from_chars(s.data(), s.data() + s.size(), v);
  if (ec != std::errc{}) {
    return std::unexpected(ec);
  }
  if (p != s.data() + s.size()) {
    return std::unexpected(std::errc::invalid_argument);
  }
  return v;
}
long sum_valid_throw(std::vector<std::string> const &in) {
  long s = 0;
  for (auto const &x : in) {
    try {
      s += parse_throw(x);
    } catch (std::invalid_argument const &) {
      s -= 1;
    }
  }
  return s;
}
long sum_valid_expected(std::vector<std::string> const &in) {
  long s = 0;
  for (auto const &x : in) {
    auto const r = parse_expected(x);
    s += r ? *r : -1;
  }
  return s;
}

// --- sort vs stable_sort, full sort vs partial_sort/nth_element ---------
struct Rec {
  int key;
  int seq;
};
long g_compares = 0;
bool by_key(Rec const &a, Rec const &b) {
  ++g_compares;
  return a.key < b.key;
}
std::vector<Rec> records(int n) {
  std::vector<Rec> v;
  for (int i = 0; i < n; ++i) {
    v.push_back({static_cast<int>((i * 2654435761U) % 1000), i});
  }
  return v;
}
std::vector<int> top_k_sort(std::vector<int> v, std::size_t k) {
  std::sort(v.begin(), v.end(), std::greater<>{});
  v.resize(k);
  return v;
}
std::vector<int> top_k_partial(std::vector<int> v, std::size_t k) {
  std::partial_sort(v.begin(), v.begin() + static_cast<long>(k), v.end(),
                    std::greater<>{});
  v.resize(k);
  return v;
}

// --- ranges views -------------------------------------------------------
long g_pred_calls = 0;
bool is_even(long x) {
  ++g_pred_calls;
  return x % 2 == 0;
}
std::vector<long> first_even_squares_baseline(std::vector<long> const &v,
                                              std::size_t k) {
  std::vector<long> evens;
  for (auto x : v) {
    if (is_even(x)) {
      evens.push_back(x);
    }
  }
  std::vector<long> squares;
  for (auto x : evens) {
    squares.push_back(x * x);
  }
  squares.resize(std::min(k, squares.size()));
  return squares;
}
std::vector<long> first_even_squares_candidate(std::vector<long> const &v,
                                               std::size_t k) {
  auto view = v | std::views::filter(is_even) |
              std::views::transform([](long x) { return x * x; }) |
              std::views::take(k);
  std::vector<long> out;
  out.reserve(k);
  std::ranges::copy(view, std::back_inserter(out));
  return out;
}
} // namespace

void verify_codegen() {
  using h::less;
  using h::require;

  // Dispatch: equal totals from every form.
  {
    std::vector<std::unique_ptr<Shape>> boxed;
    std::vector<VSquare> plain;
    std::vector<CSquare> crtp;
    std::vector<AnyShape> vars;
    for (long i = 0; i < 100; ++i) {
      boxed.push_back(std::make_unique<Square>(i));
      plain.push_back({i});
      crtp.emplace_back(i);
      vars.emplace_back(VSquare{i});
    }
    long const expect = virtual_total_baseline(boxed);
    require(template_total_candidate(plain) == expect, "template total");
    require(crtp_total_candidate(crtp) == expect, "crtp total");
    require(variant_total_candidate(vars) == expect, "variant total");
    require(variant_index_candidate(vars) == expect, "get_if total");
    boxed.push_back(std::make_unique<Rect>(2, 3));
    vars.emplace_back(VRect{2, 3});
    require(variant_total_candidate(vars) == virtual_total_baseline(boxed),
            "mixed variant total");
    require(nonfinal_area_baseline(Square{5}) ==
                final_area_candidate(FinalSquare{5}),
            "final area");
    std::printf("DISPATCH: all forms agree (%ld); see verify.sh asm\n", expect);
  }

  // std::function: allocation above the small-buffer size.
  {
    std::vector<long> v(64, 3);
    long const k = 7;
    std::array<long, 8> big{};
    big[0] = k;
    long sb = 0;
    long const ab = h::allocs([&] {
      sb = apply_function_baseline(v, [big](long x) { return x * big[0] + 1; });
    });
    long const ac = h::allocs([&] { h::sink(apply_template_candidate(v, k)); });
    require(sb == apply_template_candidate(v, k), "function equal");
    less("ALLOC", "std-function-large-capture", ab, ac);
    std::size_t largest = 0;
    auto probe = [&]<std::size_t N>() {
      std::array<char, N> cap{};
      long const a = h::allocs([&] {
        std::function<long(long)> f = [cap](long x) { return x + cap[0]; };
        h::sink(f);
      });
      if (a == 0) {
        largest = N;
      }
    };
    probe.template operator()<8>();
    probe.template operator()<16>();
    probe.template operator()<24>();
    probe.template operator()<32>();
    std::printf("SBO std::function: largest tested capture without "
                "allocation = %zu bytes (tested 8/16/24/32)\n",
                largest);
  }

  // constexpr / consteval.
  {
    std::string_view const s = "123456789";
    require(crc_static_baseline(s.data(), s.size()) == 0xCBF43926U,
            "crc check value");
    require(crc_constexpr_candidate(s.data(), s.size()) == 0xCBF43926U,
            "crc constexpr check value");
    static_assert(make_crc_table()[1] == 0x77073096U);
    for (std::string_view m : {"GET", "POST", "PUT", ""}) {
      require(route_runtime_baseline(m.data(), m.size()) ==
                  route_consteval_candidate(m.data(), m.size()),
              "route equal");
    }
    std::puts("CONSTEXPR: crc32 check value 0xCBF43926; routes agree");
  }

  // [[unlikely]]: equal results; benefit only if timing shows it.
  {
    std::vector<long> v(1000);
    for (long i = 0; i < 1000; ++i) {
      v[static_cast<std::size_t>(i)] = i % 100 == 0 ? -i : i;
    }
    require(clamp_sum_baseline(v.data(), v.size()) ==
                clamp_sum_candidate(v.data(), v.size()),
            "likely equal");
  }

  // Exceptions vs expected: same answers, including overflow and junk.
  {
    std::vector<std::string> in{"1", "x", "22", "", "3a", "99999999999"};
    require(sum_valid_throw(in) == sum_valid_expected(in), "expected equal");
    require(sum_valid_expected(in) == 1 - 1 + 22 - 1 - 1 - 1, "expected value");
    std::puts("EXPECTED: throw and expected paths agree");
  }

  // stable_sort vs sort.
  {
    auto a = records(2000);
    auto b = a;
    long const as =
        h::allocs([&] { std::stable_sort(a.begin(), a.end(), by_key); });
    long const au = h::allocs([&] { std::sort(b.begin(), b.end(), by_key); });
    require(std::ranges::equal(a, b, {}, &Rec::key, &Rec::key),
            "keys sorted equally");
    bool ties_in_order = true;
    for (std::size_t i = 1; i < a.size(); ++i) {
      if (a[i].key == a[i - 1].key && a[i].seq < a[i - 1].seq) {
        ties_in_order = false;
      }
    }
    require(ties_in_order, "stable_sort keeps tie order");
    bool unstable_ties_changed = false;
    for (std::size_t i = 1; i < b.size(); ++i) {
      if (b[i].key == b[i - 1].key && b[i].seq < b[i - 1].seq) {
        unstable_ties_changed = true;
      }
    }
    std::printf("SORT: std::sort reordered equal keys: %s\n",
                unstable_ties_changed ? "yes" : "no");
    less("ALLOC", "sort-not-stable", as, au);
  }

  // partial_sort for top-k: comparisons counted.
  {
    std::vector<int> v;
    for (int i = 0; i < 10000; ++i) {
      v.push_back(static_cast<int>((i * 2654435761U) % 100000));
    }
    long cb = 0;
    long cc = 0;
    std::vector<int> rb;
    std::vector<int> rc;
    {
      g_compares = 0;
      auto w = v;
      std::sort(w.begin(), w.end(), [](int x, int y) {
        ++g_compares;
        return x > y;
      });
      w.resize(10);
      rb = w;
      cb = g_compares;
    }
    {
      g_compares = 0;
      auto w = v;
      std::partial_sort(w.begin(), w.begin() + 10, w.end(), [](int x, int y) {
        ++g_compares;
        return x > y;
      });
      w.resize(10);
      rc = w;
      cc = g_compares;
    }
    require(rb == rc && rb == top_k_partial(v, 10) && rb == top_k_sort(v, 10),
            "top-k equal");
    less("COMPARES", "partial-sort-top-k", cb, cc);
  }

  // Ranges laziness: fewer predicate calls and allocations.
  {
    std::vector<long> v;
    for (long i = 0; i < 1000; ++i) {
      v.push_back(i);
    }
    std::vector<long> rb;
    std::vector<long> rc;
    g_pred_calls = 0;
    long const ab = h::allocs([&] { rb = first_even_squares_baseline(v, 5); });
    long const pb = g_pred_calls;
    g_pred_calls = 0;
    long const ac = h::allocs([&] { rc = first_even_squares_candidate(v, 5); });
    require(rb == rc && rb.back() == 64, "ranges equal");
    less("PREDICATE", "ranges-lazy", pb, g_pred_calls);
    less("ALLOC", "ranges-lazy", ab, ac);
  }
}

h::Pairs pairs_codegen() {
  auto boxed = std::make_shared<std::vector<std::unique_ptr<Shape>>>();
  auto plain = std::make_shared<std::vector<VSquare>>();
  auto crtp = std::make_shared<std::vector<CSquare>>();
  auto vars = std::make_shared<std::vector<AnyShape>>();
  for (long i = 0; i < 1000; ++i) {
    boxed->push_back(std::make_unique<Square>(i));
    plain->push_back({i});
    crtp->emplace_back(i);
    vars->emplace_back(VSquare{i});
  }
  auto v = std::make_shared<std::vector<long>>(1000, 3);
  auto signs = std::make_shared<std::vector<long>>();
  for (long i = 0; i < 4096; ++i) {
    signs->push_back(i % 100 == 0 ? -i : i);
  }
  auto words = std::make_shared<std::vector<std::string>>();
  for (int i = 0; i < 100; ++i) {
    words->push_back(i % 2 == 0 ? std::to_string(i) : "bad");
  }
  auto good = std::make_shared<std::vector<std::string>>();
  for (int i = 0; i < 100; ++i) {
    good->push_back(std::to_string(i));
  }
  auto recs = std::make_shared<std::vector<Rec>>(records(2000));
  auto ints = std::make_shared<std::vector<int>>();
  for (int i = 0; i < 10000; ++i) {
    ints->push_back(static_cast<int>((i * 2654435761U) % 100000));
  }
  auto seq = std::make_shared<std::vector<long>>();
  for (long i = 0; i < 1000; ++i) {
    seq->push_back(i);
  }
  static std::string const text(4096, 'q');
  auto fn = std::make_shared<std::function<long(long)>>(
      [k = 7L](long x) { return x * k + 1; });
  return {
      {"virtual-vs-template",
       [boxed] { h::sink(virtual_total_baseline(*boxed)); },
       [plain] { h::sink(template_total_candidate(*plain)); }},
      {"virtual-vs-crtp", [boxed] { h::sink(virtual_total_baseline(*boxed)); },
       [crtp] { h::sink(crtp_total_candidate(*crtp)); }},
      {"virtual-vs-variant",
       [boxed] { h::sink(virtual_total_baseline(*boxed)); },
       [vars] { h::sink(variant_total_candidate(*vars)); }},
      {"virtual-vs-variant-get-if",
       [boxed] { h::sink(virtual_total_baseline(*boxed)); },
       [vars] { h::sink(variant_index_candidate(*vars)); }},
      {"std-function-vs-template",
       [v, fn] { h::sink(apply_function_baseline(*v, *fn)); },
       [v] { h::sink(apply_template_candidate(*v, 7)); }},
      {"constexpr-table",
       [] { h::sink(crc_static_baseline(text.data(), text.size())); },
       [] { h::sink(crc_constexpr_candidate(text.data(), text.size())); }},
      {"unlikely",
       [signs] { h::sink(clamp_sum_baseline(signs->data(), signs->size())); },
       [signs] { h::sink(clamp_sum_candidate(signs->data(), signs->size())); }},
      {"expected-50pct-failure", [words] { h::sink(sum_valid_throw(*words)); },
       [words] { h::sink(sum_valid_expected(*words)); }},
      {"expected-0pct-failure", [good] { h::sink(sum_valid_throw(*good)); },
       [good] { h::sink(sum_valid_expected(*good)); }},
      {"stable-sort-vs-sort",
       [recs] {
         auto w = *recs;
         std::stable_sort(w.begin(), w.end(), by_key);
         h::sink(w);
       },
       [recs] {
         auto w = *recs;
         std::sort(w.begin(), w.end(), by_key);
         h::sink(w);
       }},
      {"partial-sort-top-k", [ints] { h::sink(top_k_sort(*ints, 10)); },
       [ints] { h::sink(top_k_partial(*ints, 10)); }},
      {"ranges-lazy", [seq] { h::sink(first_even_squares_baseline(*seq, 5)); },
       [seq] { h::sink(first_even_squares_candidate(*seq, 5)); }},
  };
}
