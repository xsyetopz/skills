#pragma once

#include <cstddef>
#include <string>
#include <vector>

// Splits s on sep. "" yields one empty field; "a,,b" yields "a", "", "b".
std::vector<std::string> split(const std::string& s, char sep);

// Number of comma-separated fields of text that are equal to word.
std::size_t count_matches(const std::string& text, const std::string& word);
