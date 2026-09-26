// Streams, formatting, and number conversion: references/io.md
#include "harness.hpp"

#include <charconv>
#include <cmath>
#include <cstdio>
#include <format>
#include <iostream>
#include <iterator>
#include <limits>
#include <memory>
#include <print>
#include <sstream>
#include <streambuf>
#include <string>
#include <string_view>
#include <system_error>
#include <vector>

namespace {
using h::require;

// Stream buffer that counts sync() calls (one per flush).
class CountingBuf : public std::streambuf {
public:
  std::string data;
  long syncs = 0;

protected:
  int_type overflow(int_type ch) override {
    if (ch != traits_type::eof()) {
      data.push_back(static_cast<char>(ch));
    }
    return ch;
  }
  std::streamsize xsputn(char const *s, std::streamsize n) override {
    data.append(s, static_cast<std::size_t>(n));
    return n;
  }
  int sync() override {
    ++syncs;
    return 0;
  }
};

void write_endl(std::ostream &out, long rows) {
  for (long i = 0; i < rows; ++i) {
    out << "row " << i << std::endl; // '\n' plus flush
  }
}
void write_newline(std::ostream &out, long rows) {
  for (long i = 0; i < rows; ++i) {
    out << "row " << i << '\n';
  }
}

// --- Integer to text ----------------------------------------------------
std::string join_ostringstream(std::vector<long> const &v) {
  std::ostringstream out;
  for (auto x : v) {
    out << x << ',';
  }
  return out.str();
}
std::string join_to_string(std::vector<long> const &v) {
  std::string out;
  for (auto x : v) {
    out += std::to_string(x); // may allocate a temporary per number
    out += ',';
  }
  return out;
}
std::string join_to_chars(std::vector<long> const &v) {
  std::string out;
  out.reserve(v.size() * 21);
  char buf[24];
  for (auto x : v) {
    auto const [end, ec] = std::to_chars(buf, buf + sizeof buf, x);
    out.append(buf, end); // ec is always success: buf fits any long
    out += ',';
  }
  return out;
}
std::string join_format_to(std::vector<long> const &v) {
  std::string out;
  out.reserve(v.size() * 21);
  auto it = std::back_inserter(out);
  for (auto x : v) {
    it = std::format_to(it, "{},", x);
  }
  return out;
}
std::string doubles_to_chars(std::vector<double> const &v) {
  std::string out;
  char buf[32];
  for (auto x : v) {
    // Shortest representation that round-trips ([charconv.to.chars]).
    auto const [end, ec] = std::to_chars(buf, buf + sizeof buf, x);
    out.append(buf, end);
    out += ',';
  }
  return out;
}

// --- Text to integer ----------------------------------------------------
long parse_stol(std::vector<std::string> const &in) {
  long s = 0;
  for (auto const &x : in) {
    s += std::stol(x); // locale-aware strtol; throws on failure
  }
  return s;
}
long parse_istringstream(std::vector<std::string> const &in) {
  long s = 0;
  for (auto const &x : in) {
    std::istringstream is(x);
    long v = 0;
    is >> v;
    s += v;
  }
  return s;
}
long parse_from_chars(std::vector<std::string> const &in) {
  long s = 0;
  for (auto const &x : in) {
    long v = 0;
    auto const [p, ec] = std::from_chars(x.data(), x.data() + x.size(), v);
    if (ec != std::errc{} || p != x.data() + x.size()) {
      h::fail("from_chars: invalid input");
    }
    s += v;
  }
  return s;
}
} // namespace

// Stdout writers compared with hyperfine; every mode prints identical
// bytes ("row N\n").
int run_printer(std::string_view mode, long rows) {
  if (mode == "print-endl") {
    write_endl(std::cout, rows);
  } else if (mode == "print-newline") {
    write_newline(std::cout, rows);
  } else if (mode == "print-nosync") {
    std::ios::sync_with_stdio(false); // before any I/O on std streams
    std::cin.tie(nullptr);
    write_newline(std::cout, rows);
  } else if (mode == "print-printf") {
    for (long i = 0; i < rows; ++i) {
      std::printf("row %ld\n", i);
    }
  } else if (mode == "print-print") {
    for (long i = 0; i < rows; ++i) {
      std::print("row {}\n", i);
    }
  } else if (mode == "print-format-to") {
    std::string buf;
    buf.reserve(1 << 16);
    for (long i = 0; i < rows; ++i) {
      std::format_to(std::back_inserter(buf), "row {}\n", i);
      if (buf.size() > (1 << 15)) {
        std::fwrite(buf.data(), 1, buf.size(), stdout);
        buf.clear();
      }
    }
    std::fwrite(buf.data(), 1, buf.size(), stdout);
  } else {
    std::fputs("unknown print mode\n", stderr);
    return 2;
  }
  return 0;
}

void verify_io() {
  using h::less;

  // endl vs '\n': identical bytes, flush count drops to zero.
  {
    CountingBuf b;
    CountingBuf c;
    std::ostream ob(&b);
    std::ostream oc(&c);
    write_endl(ob, 100);
    write_newline(oc, 100);
    require(b.data == c.data, "endl output equal");
    less("FLUSHES", "newline-not-endl", b.syncs, c.syncs);
  }

  // Number formatting: identical text, fewer allocations.
  {
    std::vector<long> v;
    for (long i = -500; i < 500; ++i) {
      v.push_back(i * 1234567890123L);
    }
    v.push_back(std::numeric_limits<long>::min());
    v.push_back(std::numeric_limits<long>::max());
    std::string a;
    std::string b;
    std::string c;
    std::string d;
    long const aa = h::allocs([&] { a = join_ostringstream(v); });
    long const ab = h::allocs([&] { b = join_to_string(v); });
    long const ac = h::allocs([&] { c = join_to_chars(v); });
    long const ad = h::allocs([&] { d = join_format_to(v); });
    require(a == b && b == c && c == d, "number text equal");
    less("ALLOC", "to-chars-vs-ostringstream", aa, ac);
    less("ALLOC", "to-chars-vs-to-string", ab, ac);
    less("ALLOC", "format-to-vs-ostringstream", aa, ad);
  }

  // Double round trip: to_chars shortest form parses back exactly.
  {
    std::vector<double> v{0.1, -0.0, 1e300, 5e-324, 3.141592653589793};
    auto const text = doubles_to_chars(v);
    std::size_t pos = 0;
    for (auto x : v) {
      auto const comma = text.find(',', pos);
      double y = 0;
      auto const [p, ec] =
          std::from_chars(text.data() + pos, text.data() + comma, y);
      require(ec == std::errc{} && p == text.data() + comma, "parse");
      require(y == x && std::signbit(y) == std::signbit(x), "round trip");
      pos = comma + 1;
    }
    std::printf("TO_CHARS double shortest: %s\n", text.c_str());
  }

  // Parsing: same sums; from_chars allocates nothing.
  {
    std::vector<std::string> in;
    for (long i = 0; i < 200; ++i) {
      in.push_back(std::to_string(i * 7919 - 50000));
    }
    long sa = 0;
    long sb = 0;
    long sc = 0;
    long const aa = h::allocs([&] { sa = parse_stol(in); });
    long const ab = h::allocs([&] { sb = parse_istringstream(in); });
    long const ac = h::allocs([&] { sc = parse_from_chars(in); });
    require(sa == sb && sb == sc, "parse sums equal");
    h::same("ALLOC", "from-chars-vs-stol", aa, ac);
    h::same("ALLOC", "from-chars-vs-istringstream", ab, ac);
    // Semantic differences the rewrite must handle explicitly.
    long v = 0;
    std::string_view const ws = " 42";
    auto const r1 = std::from_chars(ws.data(), ws.data() + ws.size(), v);
    require(r1.ec == std::errc::invalid_argument,
            "from_chars rejects leading whitespace (stol accepts it)");
    std::string_view const plus = "+42";
    auto const r2 = std::from_chars(plus.data(), plus.data() + 3, v);
    require(r2.ec == std::errc::invalid_argument,
            "from_chars rejects a leading plus (stol accepts it)");
    std::string_view const big = "99999999999999999999";
    auto const r3 = std::from_chars(big.data(), big.data() + big.size(), v);
    require(r3.ec == std::errc::result_out_of_range, "overflow reported");
    std::puts("FROM_CHARS: rejects ' 42' and '+42'; reports overflow");
  }
}

h::Pairs pairs_io() {
  auto v = std::make_shared<std::vector<long>>();
  for (long i = 0; i < 1000; ++i) {
    v->push_back(i * 1234567L);
  }
  auto in = std::make_shared<std::vector<std::string>>();
  for (long i = 0; i < 1000; ++i) {
    in->push_back(std::to_string(i * 7919 - 50000));
  }
  return {
      {"to-chars-vs-ostringstream", [v] { h::sink(join_ostringstream(*v)); },
       [v] { h::sink(join_to_chars(*v)); }},
      {"to-chars-vs-to-string", [v] { h::sink(join_to_string(*v)); },
       [v] { h::sink(join_to_chars(*v)); }},
      {"format-to-vs-ostringstream", [v] { h::sink(join_ostringstream(*v)); },
       [v] { h::sink(join_format_to(*v)); }},
      {"from-chars-vs-stol", [in] { h::sink(parse_stol(*in)); },
       [in] { h::sink(parse_from_chars(*in)); }},
      {"from-chars-vs-istringstream",
       [in] { h::sink(parse_istringstream(*in)); },
       [in] { h::sink(parse_from_chars(*in)); }},
  };
}
