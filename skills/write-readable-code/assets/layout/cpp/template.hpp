#pragma once

#include <cstddef>

namespace project {

inline constexpr std::size_t kPublicLimit = 128;

class PublicType {
public:
  PublicType();

  void public_method();

private:
  void private_method();
};

} // namespace project
