#include "match.hpp"

std::vector<std::string> split(const std::string& s, char sep)
{
    std::vector<std::string> out;
    std::size_t start = 0;
    while (true) {
        auto end = s.find(sep, start);
        std::string field = s.substr(start, end - start);
        out.push_back(field);
        if (end == std::string::npos)
            break;
        start = end + 1;
    }
    return out;
}

std::size_t count_matches(const std::string& text, const std::string& word)
{
    std::size_t n = 0;
    for (const auto& field : split(text, ','))
        if (field == word)
            ++n;
    return n;
}
