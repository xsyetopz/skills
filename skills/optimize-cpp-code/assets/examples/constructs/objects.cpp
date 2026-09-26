// Moves, copies, parameters, and ownership: references/objects.md
#include "harness.hpp"

#include <cstdio>
#include <memory>
#include <string>
#include <vector>

namespace {
using h::Item;
using h::require;

// Long enough to exceed the libc++ short-string buffer on 64-bit targets.
std::string const kLong(64, 'x');

// --- Guaranteed copy elision (C++17 prvalues) ---------------------------
Item make_item(int v) { return Item{v}; }

// Baseline: std::move on a prvalue materializes a temporary and moves it.
__attribute__((noinline)) int elide_baseline(int v) {
  Item a = std::move(make_item(v));
  return a.value;
}
// Candidate: the prvalue initializes a directly; no temporary exists.
__attribute__((noinline)) int elide_candidate(int v) {
  Item a = make_item(v);
  return a.value;
}

// --- NRVO and return std::move(local) -----------------------------------
__attribute__((noinline)) Item nrvo_baseline(int v) {
  Item r{v};
  r.value += 1;
  return std::move(r); // -Wpessimizing-move: disables NRVO
}
__attribute__((noinline)) Item nrvo_candidate(int v) {
  Item r{v};
  r.value += 1;
  return r; // NRVO, or an implicit move if elision is not done
}

// --- Implicit move on return ([expr.prim.id.unqual], P2266) -------------
__attribute__((noinline)) Item ret_param_baseline(Item t) {
  t.value += 1;
  return std::move(t); // -Wredundant-move
}
__attribute__((noinline)) Item ret_param_candidate(Item t) {
  t.value += 1;
  return t; // move-eligible: moved, never copied
}
// C++23: an rvalue-reference parameter named in return is move-eligible.
__attribute__((noinline)) Item ret_rref_candidate(Item &&t) { return t; }

// --- const locals cannot be moved from ----------------------------------
__attribute__((noinline)) void const_local_baseline(std::vector<Item> &out,
                                                    int v) {
  Item const t{v};
  out.push_back(std::move(t)); // const Item&& binds to the copy ctor
}
__attribute__((noinline)) void const_local_candidate(std::vector<Item> &out,
                                                     int v) {
  Item t{v};
  out.push_back(std::move(t));
}

// --- std::move at the last use ------------------------------------------
std::vector<std::string> collect_baseline(int n) {
  std::vector<std::string> out;
  out.reserve(static_cast<std::size_t>(n));
  for (int i = 0; i < n; ++i) {
    std::string line = kLong;
    line += std::to_string(i);
    out.push_back(line); // copy: second heap allocation per line
  }
  return out;
}
std::vector<std::string> collect_candidate(int n) {
  std::vector<std::string> out;
  out.reserve(static_cast<std::size_t>(n));
  for (int i = 0; i < n; ++i) {
    std::string line = kLong;
    line += std::to_string(i);
    out.push_back(std::move(line)); // last use: steal the buffer
  }
  return out;
}

// --- noexcept move constructor and vector growth ------------------------
template <class T> std::vector<T> grow(int n) {
  std::vector<T> v;
  for (int i = 0; i < n; ++i) {
    v.emplace_back(i);
  }
  return v;
}

// --- Pass by value and move (sink parameter) ----------------------------
struct WidgetRef {
  std::string name;
  void set(std::string const &s) { name = s; }
};
struct WidgetVal {
  std::string name;
  void set(std::string s) { name = std::move(s); }
};

// --- const& for read-only parameters ------------------------------------
__attribute__((noinline)) std::size_t
total_len_baseline(std::vector<std::string> v) {
  std::size_t n = 0;
  for (auto const &s : v) {
    n += s.size();
  }
  return n;
}
__attribute__((noinline)) std::size_t
total_len_candidate(std::vector<std::string> const &v) {
  std::size_t n = 0;
  for (auto const &s : v) {
    n += s.size();
  }
  return n;
}

// --- emplace_back vs push_back ------------------------------------------
void push_items(std::vector<Item> &v, int n) {
  for (int i = 0; i < n; ++i) {
    v.push_back(Item{i}); // constructs a temporary, then moves it
  }
}
void emplace_items(std::vector<Item> &v, int n) {
  for (int i = 0; i < n; ++i) {
    v.emplace_back(i); // constructs in place
  }
}

// --- make_shared --------------------------------------------------------
struct Node {
  long value;
  explicit Node(long v) : value(v) {}
};
std::shared_ptr<Node> shared_new(long v) {
  return std::shared_ptr<Node>(new Node(v));
}
std::shared_ptr<Node> shared_make(long v) { return std::make_shared<Node>(v); }
} // namespace

// --- shared_ptr copies vs references (assembly checked) -----------------
extern "C" {
// The empty asm keeps each call in the loop (no hoisting of a pure call).
__attribute__((noinline)) long read_by_value(std::shared_ptr<long> p) {
  h::clobber();
  return *p;
}
__attribute__((noinline)) long read_by_ref(std::shared_ptr<long> const &p) {
  h::clobber();
  return *p;
}
__attribute__((noinline)) long read_unique(std::unique_ptr<long> const &p) {
  return *p;
}
__attribute__((noinline)) long
shared_by_value_baseline(std::shared_ptr<long> const &p, int n) {
  long s = 0;
  for (int i = 0; i < n; ++i) {
    s += read_by_value(p); // copy: atomic increment and decrement
  }
  return s;
}
__attribute__((noinline)) long
shared_by_ref_candidate(std::shared_ptr<long> const &p, int n) {
  long s = 0;
  for (int i = 0; i < n; ++i) {
    s += read_by_ref(p);
  }
  return s;
}
// unique_ptr: moving ownership is a pointer copy plus a null store.
__attribute__((noinline)) void
shared_handoff_baseline(std::shared_ptr<long> const &p,
                        std::shared_ptr<long> *out) {
  *out = p; // copy of a shared_ptr: atomic increment
}
__attribute__((noinline)) void
unique_handoff_candidate(std::unique_ptr<long> &p, std::unique_ptr<long> *out) {
  *out = std::move(p); // pointer copy, source set to null
}
}

void verify_objects() {
  using h::less;
  using h::reset_tracked;
  using h::same;
  using h::tracked;

  // Copy elision.
  reset_tracked();
  require(elide_baseline(7) == 7, "elide baseline value");
  long const elide_b = tracked.moves + tracked.copies;
  reset_tracked();
  require(elide_candidate(7) == 7, "elide candidate value");
  less("MOVES", "copy-elision", elide_b, tracked.moves + tracked.copies);

  // NRVO.
  reset_tracked();
  require(nrvo_baseline(1).value == 2, "nrvo baseline value");
  long const nrvo_b = tracked.moves + tracked.copies;
  reset_tracked();
  require(nrvo_candidate(1).value == 2, "nrvo candidate value");
  less("MOVES", "nrvo", nrvo_b, tracked.moves + tracked.copies);

  // Implicit move: same cost as the explicit std::move, never a copy.
  reset_tracked();
  require(ret_param_baseline(Item{1}).value == 2, "ret param baseline");
  long const rp_b = tracked.moves;
  require(tracked.copies == 0, "explicit move copied");
  reset_tracked();
  require(ret_param_candidate(Item{1}).value == 2, "ret param candidate");
  require(tracked.copies == 0, "implicit move copied");
  same("MOVES", "implicit-move-param", rp_b, tracked.moves);
  reset_tracked();
  require(ret_rref_candidate(Item{3}).value == 3, "rref value");
  std::printf("COPIES implicit-move-rref (C++23): %ld (moves %ld)\n",
              tracked.copies, tracked.moves);
#if __cplusplus > 202002L
  require(tracked.copies == 0, "C++23 return of T&& param copied");
#endif

  // const local.
  {
    std::vector<Item> out;
    out.reserve(4);
    reset_tracked();
    const_local_baseline(out, 1);
    long const cb = tracked.copies;
    reset_tracked();
    const_local_candidate(out, 1);
    less("COPIES", "const-local", cb, tracked.copies);
    require(out[0] == out[1], "const-local values");
  }

  // std::move at last use.
  {
    std::vector<std::string> b;
    std::vector<std::string> c;
    long const ab = h::allocs([&] { b = collect_baseline(256); });
    long const ac = h::allocs([&] { c = collect_candidate(256); });
    require(b == c, "collect equal");
    less("ALLOC", "move-last-use", ab, ac);
  }

  // noexcept move and growth.
  {
    reset_tracked();
    auto const vb = grow<h::Tracked<false>>(1000);
    long const cb = tracked.copies;
    reset_tracked();
    auto const vc = grow<h::Tracked<true>>(1000);
    require(vb.size() == vc.size() && vb.back().value == vc.back().value,
            "grow equal");
    less("COPIES", "noexcept-move", cb, tracked.copies);
    std::printf("MOVES noexcept-move candidate relocations: %ld\n",
                tracked.moves);
  }

  // Sink parameter: rvalue argument.
  {
    WidgetRef r;
    WidgetVal v;
    long const ab = h::allocs([&] { r.set(std::string(kLong)); });
    long const ac = h::allocs([&] { v.set(std::string(kLong)); });
    require(r.name == v.name, "sink rvalue equal");
    less("ALLOC", "sink-param-rvalue", ab, ac);
    // Lvalue argument into a target with enough capacity: const& reuses
    // the existing buffer; by-value must copy into a new string first.
    std::string const shorter(40, 'y');
    long const lb = h::allocs([&] { r.set(shorter); });
    long const lc = h::allocs([&] { v.set(shorter); });
    require(r.name == v.name, "sink lvalue equal");
    h::less("ALLOC", "sink-param-lvalue-reuse", lc, lb);
  }

  // const& read-only parameter.
  {
    std::vector<std::string> const names(64, kLong);
    std::size_t sb = 0;
    std::size_t sc = 0;
    long const ab = h::allocs([&] { sb = total_len_baseline(names); });
    long const ac = h::allocs([&] { sc = total_len_candidate(names); });
    require(sb == sc, "total_len equal");
    less("ALLOC", "const-ref-param", ab, ac);
  }

  // emplace_back.
  {
    std::vector<Item> b;
    std::vector<Item> c;
    b.reserve(64);
    c.reserve(64);
    reset_tracked();
    push_items(b, 64);
    long const mb = tracked.moves;
    reset_tracked();
    emplace_items(c, 64);
    require(b == c, "emplace equal");
    less("MOVES", "emplace-back", mb, tracked.moves);
    // With an existing object both do the same copy.
    Item const existing{5};
    reset_tracked();
    b.push_back(existing);
    long const pb = tracked.copies;
    reset_tracked();
    c.emplace_back(existing);
    same("COPIES", "emplace-back-lvalue", pb, tracked.copies);
  }

  // make_shared.
  {
    std::shared_ptr<Node> b;
    std::shared_ptr<Node> c;
    long const ab = h::allocs([&] { b = shared_new(9); });
    long const ac = h::allocs([&] { c = shared_make(9); });
    require(b->value == c->value, "make_shared equal");
    less("ALLOC", "make-shared", ab, ac);
  }

  // shared_ptr by const& and unique_ptr: results equal; the benefit is
  // asserted in the assembly (verify.sh asm).
  {
    auto const p = std::make_shared<long>(3);
    require(shared_by_value_baseline(p, 10) == shared_by_ref_candidate(p, 10),
            "shared by ref equal");
    require(p.use_count() == 1, "no leaked references");
    auto u = std::make_unique<long>(4);
    require(read_unique(u) == 4, "unique read");
    std::unique_ptr<long> moved;
    unique_handoff_candidate(u, &moved);
    require(!u && *moved == 4, "unique handoff");
    std::shared_ptr<long> shared;
    shared_handoff_baseline(p, &shared);
    require(p.use_count() == 2 && *shared == 3, "shared handoff");
    std::printf("SIZE shared-vs-unique: sizeof shared_ptr %zu, "
                "unique_ptr %zu\n",
                sizeof(std::shared_ptr<long>), sizeof(std::unique_ptr<long>));
    require(sizeof(std::unique_ptr<long>) < sizeof(std::shared_ptr<long>),
            "unique_ptr smaller");
  }
}

h::Pairs pairs_objects() {
  auto const names =
      std::make_shared<std::vector<std::string>>(64, std::string(kLong));
  auto const sp =
      std::make_shared<std::shared_ptr<long>>(std::make_shared<long>(1));
  return {
      {"move-last-use", [] { h::sink(collect_baseline(256)); },
       [] { h::sink(collect_candidate(256)); }},
      {"noexcept-move", [] { h::sink(grow<h::Tracked<false>>(1000)); },
       [] { h::sink(grow<h::Tracked<true>>(1000)); }},
      {"const-ref-param", [names] { h::sink(total_len_baseline(*names)); },
       [names] { h::sink(total_len_candidate(*names)); }},
      {"make-shared", [] { h::sink(shared_new(1)); },
       [] { h::sink(shared_make(1)); }},
      {"shared-by-ref", [sp] { h::sink(shared_by_value_baseline(*sp, 1000)); },
       [sp] { h::sink(shared_by_ref_candidate(*sp, 1000)); }},
  };
}
