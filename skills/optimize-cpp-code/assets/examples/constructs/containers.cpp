// Containers, strings, views, and allocators: references/containers.md
#include "harness.hpp"

#include <algorithm>
#include <array>
#include <cstdio>
#include <flat_map>
#include <functional>
#include <map>
#include <memory_resource>
#include <numeric>
#include <span>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace {
using h::require;

// --- reserve ------------------------------------------------------------
std::vector<long> squares_baseline(int n) {
  std::vector<long> v;
  for (int i = 0; i < n; ++i) {
    v.push_back(long{i} * i);
  }
  return v;
}
std::vector<long> squares_candidate(int n) {
  std::vector<long> v;
  v.reserve(static_cast<std::size_t>(n));
  for (int i = 0; i < n; ++i) {
    v.push_back(long{i} * i);
  }
  return v;
}

// --- clear() and reuse --------------------------------------------------
std::size_t widest_baseline(std::vector<std::string> const &lines) {
  std::size_t widest = 0;
  for (auto const &line : lines) {
    std::vector<std::string_view> fields; // new buffer per line
    std::size_t start = 0;
    while (start <= line.size()) {
      auto end = line.find(' ', start);
      if (end == std::string::npos) {
        end = line.size();
      }
      fields.push_back(std::string_view(line).substr(start, end - start));
      start = end + 1;
    }
    widest = std::max(widest, fields.size());
  }
  return widest;
}
std::size_t widest_candidate(std::vector<std::string> const &lines) {
  std::size_t widest = 0;
  std::vector<std::string_view> fields; // capacity kept across lines
  for (auto const &line : lines) {
    fields.clear();
    std::size_t start = 0;
    while (start <= line.size()) {
      auto end = line.find(' ', start);
      if (end == std::string::npos) {
        end = line.size();
      }
      fields.push_back(std::string_view(line).substr(start, end - start));
      start = end + 1;
    }
    widest = std::max(widest, fields.size());
  }
  return widest;
}

// --- string_view parameters and substrings ------------------------------
std::vector<std::size_t> field_lengths_baseline(std::string const &text) {
  std::vector<std::size_t> out;
  std::size_t start = 0;
  while (true) {
    auto const end = text.find(':', start);
    auto const n = end == std::string::npos ? text.size() - start : end - start;
    std::string const field = text.substr(start, n); // owning copy
    out.push_back(field.size());
    if (end == std::string::npos) {
      break;
    }
    start = end + 1;
  }
  return out;
}
std::vector<std::size_t> field_lengths_candidate(std::string_view text) {
  std::vector<std::size_t> out;
  std::size_t start = 0;
  while (true) {
    auto const end = text.find(':', start);
    auto const n =
        end == std::string_view::npos ? text.size() - start : end - start;
    std::string_view const field = text.substr(start, n); // no copy
    out.push_back(field.size());
    if (end == std::string_view::npos) {
      break;
    }
    start = end + 1;
  }
  return out;
}
__attribute__((noinline)) bool is_admin_baseline(std::string const &name) {
  return name.starts_with("administrator-account-");
}
__attribute__((noinline)) bool is_admin_candidate(std::string_view name) {
  return name.starts_with("administrator-account-");
}

// --- std::span parameters -----------------------------------------------
__attribute__((noinline)) long sum_baseline(std::vector<long> const &v) {
  return std::accumulate(v.begin(), v.end(), 0L);
}
__attribute__((noinline)) long sum_candidate(std::span<long const> v) {
  return std::accumulate(v.begin(), v.end(), 0L);
}

// --- unordered_map reserve and single lookup ----------------------------
std::unordered_map<long, long> index_baseline(int n) {
  std::unordered_map<long, long> m;
  for (int i = 0; i < n; ++i) {
    m.emplace(i, i);
  }
  return m;
}
std::unordered_map<long, long> index_candidate(int n) {
  std::unordered_map<long, long> m;
  m.reserve(static_cast<std::size_t>(n));
  for (int i = 0; i < n; ++i) {
    m.emplace(i, i);
  }
  return m;
}

long g_hashes = 0;
struct CountingHash {
  std::size_t operator()(std::string const &s) const {
    ++g_hashes;
    return std::hash<std::string>{}(s);
  }
};
using Counter = std::unordered_map<std::string, long, CountingHash>;
void count_words_baseline(Counter &m, std::vector<std::string> const &ws) {
  for (auto const &w : ws) {
    if (m.find(w) == m.end()) { // lookup 1
      m.emplace(w, 1);          // lookup 2 on a miss
    } else {
      m[w] += 1; // lookup 2 on a hit
    }
  }
}
void count_words_candidate(Counter &m, std::vector<std::string> const &ws) {
  for (auto const &w : ws) {
    auto [it, inserted] = m.try_emplace(w, 0); // one lookup
    it->second += 1;
  }
}

// --- Heterogeneous lookup (C++20 transparent hash) -----------------------
struct StringHash {
  using is_transparent = void;
  std::size_t operator()(std::string_view s) const {
    return std::hash<std::string_view>{}(s);
  }
};
using PlainMap = std::unordered_map<std::string, long>;
using HeteroMap =
    std::unordered_map<std::string, long, StringHash, std::equal_to<>>;
long lookup_baseline(PlainMap const &m,
                     std::vector<std::string_view> const &keys) {
  long s = 0;
  for (auto k : keys) {
    auto const it = m.find(std::string(k)); // temporary key string
    s += it == m.end() ? 0 : it->second;
  }
  return s;
}
long lookup_candidate(HeteroMap const &m,
                      std::vector<std::string_view> const &keys) {
  long s = 0;
  for (auto k : keys) {
    auto const it = m.find(k); // no std::string constructed
    s += it == m.end() ? 0 : it->second;
  }
  return s;
}

// --- Sorted vector, std::map, std::flat_map -----------------------------
std::map<long, long> build_map(std::vector<long> const &keys) {
  std::map<long, long> m;
  for (auto k : keys) {
    m.emplace(k, k * 2);
  }
  return m;
}
std::vector<std::pair<long, long>> build_sorted(std::vector<long> const &keys) {
  std::vector<std::pair<long, long>> v;
  v.reserve(keys.size());
  for (auto k : keys) {
    v.emplace_back(k, k * 2);
  }
  std::sort(v.begin(), v.end());
  return v;
}
std::flat_map<long, long> build_flat(std::vector<long> const &keys) {
  std::vector<long> ks;
  std::vector<long> vs;
  ks.reserve(keys.size());
  vs.reserve(keys.size());
  auto sorted = keys;
  std::sort(sorted.begin(), sorted.end());
  for (auto k : sorted) {
    ks.push_back(k);
    vs.push_back(k * 2);
  }
  // sorted_unique skips the sort and duplicate check (precondition).
  return std::flat_map<long, long>(std::sorted_unique, std::move(ks),
                                   std::move(vs));
}
long probe_map(std::map<long, long> const &m, std::vector<long> const &q) {
  long s = 0;
  for (auto k : q) {
    auto const it = m.find(k);
    s += it == m.end() ? -1 : it->second;
  }
  return s;
}
long probe_sorted(std::vector<std::pair<long, long>> const &v,
                  std::vector<long> const &q) {
  long s = 0;
  for (auto k : q) {
    auto const it =
        std::lower_bound(v.begin(), v.end(), k,
                         [](auto const &e, long key) { return e.first < key; });
    s += (it == v.end() || it->first != k) ? -1 : it->second;
  }
  return s;
}
long probe_flat(std::flat_map<long, long> const &m,
                std::vector<long> const &q) {
  long s = 0;
  for (auto k : q) {
    auto const it = m.find(k);
    s += it == m.end() ? -1 : it->second;
  }
  return s;
}
long probe_unordered(std::unordered_map<long, long> const &m,
                     std::vector<long> const &q) {
  long s = 0;
  for (auto k : q) {
    auto const it = m.find(k);
    s += it == m.end() ? -1 : it->second;
  }
  return s;
}

// --- std::pmr::monotonic_buffer_resource --------------------------------
std::size_t request_baseline(int n) {
  std::vector<std::string> parts;
  for (int i = 0; i < n; ++i) {
    parts.emplace_back(40, static_cast<char>('a' + i % 26));
  }
  std::size_t total = 0;
  for (auto const &p : parts) {
    total += p.size();
  }
  return total;
}
std::size_t request_candidate(int n) {
  std::array<std::byte, 16384> buffer;
  // null_memory_resource upstream: overflow throws bad_alloc instead of
  // silently falling back to the heap (drop it to allow fallback).
  std::pmr::monotonic_buffer_resource arena(buffer.data(), buffer.size(),
                                            std::pmr::null_memory_resource());
  std::pmr::vector<std::pmr::string> parts(&arena);
  for (int i = 0; i < n; ++i) {
    parts.emplace_back(40, static_cast<char>('a' + i % 26));
  }
  std::size_t total = 0;
  for (auto const &p : parts) {
    total += p.size();
  }
  return total;
}

// --- std::erase_if vs erase in a loop ------------------------------------
void drop_zero_baseline(std::vector<h::Item> &v) {
  for (auto it = v.begin(); it != v.end();) {
    if (it->value == 0) {
      it = v.erase(it); // shifts the whole tail each time
    } else {
      ++it;
    }
  }
}
void drop_zero_candidate(std::vector<h::Item> &v) {
  std::erase_if(v, [](h::Item const &x) { return x.value == 0; });
}
std::vector<h::Item> zero_every_third(int n) {
  std::vector<h::Item> v;
  v.reserve(static_cast<std::size_t>(n));
  for (int i = 0; i < n; ++i) {
    v.emplace_back(i % 3 == 0 ? 0 : i);
  }
  return v;
}
} // namespace

void verify_containers() {
  using h::less;
  using h::same;

  // reserve.
  {
    std::vector<long> b;
    std::vector<long> c;
    long const ab = h::allocs([&] { b = squares_baseline(1000); });
    long const ac = h::allocs([&] { c = squares_candidate(1000); });
    require(b == c && squares_candidate(0).empty(), "reserve equal");
    less("ALLOC", "reserve", ab, ac);
    // Pointers survive push_back only while size() < capacity().
    std::vector<int> v;
    v.reserve(2);
    v.push_back(1);
    int const *const saved = v.data();
    v.push_back(2);
    require(saved == v.data(), "no reallocation within capacity");
    v.push_back(3);
    std::printf("INVALIDATE reserve: data() moved after exceeding "
                "capacity: %s\n",
                saved != v.data() ? "yes" : "no (allocator reused block)");
  }

  // shrink_to_fit.
  {
    std::vector<long> v;
    v.reserve(4096);
    v.resize(10);
    auto const before = v.capacity();
    long const a = h::allocs([&] { v.shrink_to_fit(); });
    std::printf("CAPACITY shrink-to-fit: %zu -> %zu elements (%ld alloc)\n",
                before, v.capacity(), a);
    require(v.capacity() < before && v.size() == 10, "shrink_to_fit");
  }

  // clear and reuse.
  {
    std::vector<std::string> lines;
    for (int i = 0; i < 64; ++i) {
      lines.push_back("alpha beta gamma delta " + std::to_string(i));
    }
    lines.emplace_back();
    std::size_t wb = 0;
    std::size_t wc = 0;
    long const ab = h::allocs([&] { wb = widest_baseline(lines); });
    long const ac = h::allocs([&] { wc = widest_candidate(lines); });
    require(wb == wc && wb == 5, "widest equal");
    less("ALLOC", "clear-reuse", ab, ac);
  }

  // SSO: find the largest length that does not allocate.
  {
    std::size_t largest = 0;
    for (std::size_t n = 0; n < 64; ++n) {
      long const a = h::allocs([&] {
        std::string s(n, 'k');
        h::sink(s);
      });
      if (a == 0) {
        largest = n;
      }
    }
    std::printf("SSO: std::string{}.capacity() = %zu; largest length "
                "without allocation = %zu\n",
                std::string{}.capacity(), largest);
    long const at = h::allocs([&] {
      std::string s(largest, 'k');
      h::sink(s);
    });
    long const over = h::allocs([&] {
      std::string s(largest + 1, 'k');
      h::sink(s);
    });
    less("ALLOC", "sso-boundary", over, at);
  }

  // string_view substrings and parameters.
  {
    std::string text;
    for (int i = 0; i < 32; ++i) {
      text += std::string(30, 'f') + ":";
    }
    text += "\xc3\xa9"; // non-ASCII tail: byte lengths, not characters
    std::vector<std::size_t> b;
    std::vector<std::size_t> c;
    long const ab = h::allocs([&] { b = field_lengths_baseline(text); });
    long const ac = h::allocs([&] { c = field_lengths_candidate(text); });
    require(b == c && b.back() == 2, "field lengths equal");
    require(field_lengths_candidate("") == std::vector<std::size_t>{0},
            "empty text");
    require(field_lengths_candidate(std::string("a\0:b", 4)) ==
                std::vector<std::size_t>({2, 1}),
            "embedded NUL");
    less("ALLOC", "string-view-substr", ab, ac);
    char const *raw = "administrator-account-7";
    bool rb = false;
    bool rc = false;
    long const pb = h::allocs([&] { rb = is_admin_baseline(raw); });
    long const pc = h::allocs([&] { rc = is_admin_candidate(raw); });
    require(rb && rc, "is_admin equal");
    less("ALLOC", "string-view-param", pb, pc);
  }

  // span.
  {
    std::array<long, 256> data{};
    std::iota(data.begin(), data.end(), 1);
    long sb = 0;
    long sc = 0;
    long const ab = h::allocs([&] {
      sb = sum_baseline(std::vector<long>(data.begin(), data.end()));
    });
    long const ac = h::allocs([&] { sc = sum_candidate(data); });
    require(sb == sc && sb == 256 * 257 / 2, "span sum equal");
    less("ALLOC", "span-param", ab, ac);
  }

  // unordered_map reserve.
  {
    std::unordered_map<long, long> b;
    std::unordered_map<long, long> c;
    long const ab = h::allocs([&] { b = index_baseline(1000); });
    long const ac = h::allocs([&] { c = index_candidate(1000); });
    require(b == c, "index equal");
    less("ALLOC", "unordered-reserve", ab, ac);
  }

  // try_emplace: one hash per word.
  {
    std::vector<std::string> words;
    for (int i = 0; i < 300; ++i) {
      words.push_back("w" + std::to_string(i % 50));
    }
    Counter b;
    Counter c;
    b.reserve(64);
    c.reserve(64);
    g_hashes = 0;
    count_words_baseline(b, words);
    long const hb = g_hashes;
    g_hashes = 0;
    count_words_candidate(c, words);
    require(b == c && b.at("w7") == 6, "word counts equal");
    less("HASHES", "try-emplace", hb, g_hashes);
  }

  // Heterogeneous lookup.
  {
    PlainMap pm;
    HeteroMap hm;
    std::vector<std::string> owners;
    for (int i = 0; i < 64; ++i) {
      owners.push_back("customer-account-identifier-" + std::to_string(i));
      pm.emplace(owners.back(), i);
      hm.emplace(owners.back(), i);
    }
    std::vector<std::string_view> keys(owners.begin(), owners.end());
    keys.push_back("customer-account-identifier-missing");
    long sb = 0;
    long sc = 0;
    long const ab = h::allocs([&] { sb = lookup_baseline(pm, keys); });
    long const ac = h::allocs([&] { sc = lookup_candidate(hm, keys); });
    require(sb == sc && sb == 63 * 64 / 2, "hetero lookup equal");
    less("ALLOC", "heterogeneous-lookup", ab, ac);
  }

  // Sorted vector / flat_map / map: equal answers; build allocations.
  {
    std::vector<long> keys;
    for (long i = 0; i < 1000; ++i) {
      keys.push_back((i * 7919) % 1000 * 3);
    }
    std::vector<long> probes;
    for (long i = 0; i < 3000; ++i) {
      probes.push_back(i);
    }
    std::map<long, long> m;
    std::vector<std::pair<long, long>> sv;
    std::flat_map<long, long> fm;
    long const am = h::allocs([&] { m = build_map(keys); });
    long const as = h::allocs([&] { sv = build_sorted(keys); });
    long const af = h::allocs([&] { fm = build_flat(keys); });
    long const expect = probe_map(m, probes);
    require(probe_sorted(sv, probes) == expect, "sorted vector equal");
    require(probe_flat(fm, probes) == expect, "flat_map equal");
    less("ALLOC", "sorted-vector-build", am, as);
    less("ALLOC", "flat-map-build", am, af);
  }

  // pmr arena.
  {
    std::size_t b = 0;
    std::size_t c = 0;
    long const ab = h::allocs([&] { b = request_baseline(64); });
    long const ac = h::allocs([&] { c = request_candidate(64); });
    require(b == c && b == 64 * 40, "pmr equal");
    less("ALLOC", "pmr-monotonic", ab, ac);
    bool threw = false;
    try {
      h::sink(request_candidate(1024)); // exceeds the 16 KiB buffer
    } catch (std::bad_alloc const &) {
      threw = true;
    }
    require(threw, "null upstream must throw on overflow");
    std::puts("PMR overflow with null_memory_resource: bad_alloc thrown");
  }

  // erase_if.
  {
    auto b = zero_every_third(900);
    auto c = b;
    h::reset_tracked();
    drop_zero_baseline(b);
    long const mb = h::tracked.moves;
    h::reset_tracked();
    drop_zero_candidate(c);
    require(b == c && b.size() == 600, "erase_if equal");
    less("MOVES", "erase-if", mb, h::tracked.moves);
  }
}

h::Pairs pairs_containers() {
  auto keys = std::make_shared<std::vector<long>>();
  auto probes = std::make_shared<std::vector<long>>();
  for (long i = 0; i < 1000; ++i) {
    keys->push_back((i * 7919) % 1000 * 3);
  }
  for (long i = 0; i < 3000; ++i) {
    probes->push_back((i * 2654435761L) % 3000);
  }
  auto m = std::make_shared<std::map<long, long>>(build_map(*keys));
  auto sv =
      std::make_shared<std::vector<std::pair<long, long>>>(build_sorted(*keys));
  auto fm = std::make_shared<std::flat_map<long, long>>(build_flat(*keys));
  auto um = std::make_shared<std::unordered_map<long, long>>();
  for (auto k : *keys) {
    um->emplace(k, k * 2);
  }
  auto text = std::make_shared<std::string>();
  for (int i = 0; i < 32; ++i) {
    *text += std::string(30, 'f') + ":";
  }
  auto erase_input =
      std::make_shared<std::vector<h::Item>>(zero_every_third(900));
  return {
      {"reserve", [] { h::sink(squares_baseline(1000)); },
       [] { h::sink(squares_candidate(1000)); }},
      {"string-view-substr", [text] { h::sink(field_lengths_baseline(*text)); },
       [text] { h::sink(field_lengths_candidate(*text)); }},
      {"unordered-reserve", [] { h::sink(index_baseline(1000)); },
       [] { h::sink(index_candidate(1000)); }},
      {"lookup-map-vs-sorted-vector",
       [m, probes] { h::sink(probe_map(*m, *probes)); },
       [sv, probes] { h::sink(probe_sorted(*sv, *probes)); }},
      {"lookup-map-vs-flat-map",
       [m, probes] { h::sink(probe_map(*m, *probes)); },
       [fm, probes] { h::sink(probe_flat(*fm, *probes)); }},
      {"lookup-flat-map-vs-unordered",
       [fm, probes] { h::sink(probe_flat(*fm, *probes)); },
       [um, probes] { h::sink(probe_unordered(*um, *probes)); }},
      {"pmr-monotonic", [] { h::sink(request_baseline(64)); },
       [] { h::sink(request_candidate(64)); }},
      {"erase-if",
       [erase_input] {
         auto v = *erase_input;
         drop_zero_baseline(v);
         h::sink(v);
       },
       [erase_input] {
         auto v = *erase_input;
         drop_zero_candidate(v);
         h::sink(v);
       }},
  };
}
