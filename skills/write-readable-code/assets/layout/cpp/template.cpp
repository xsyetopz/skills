#include "component.hpp" // own header first proves it is self-contained

#include <cstddef>

namespace project {

namespace {
constexpr std::size_t kPrivateLimit = 64;

std::size_t private_helper(std::size_t value) {
  return value < kPrivateLimit ? value : kPrivateLimit;
}
} // namespace

PublicType::PublicType() = default;

void PublicType::public_method() { private_method(); }

void PublicType::private_method() {
  static_cast<void>(private_helper(kPublicLimit));
}

} // namespace project
