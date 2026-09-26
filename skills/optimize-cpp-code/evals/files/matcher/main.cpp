#include "match.hpp"

#include <fstream>
#include <iostream>
#include <sstream>

// Usage: matcher FILE WORD. Counts WORD among the comma-separated fields of
// every line of FILE.
int main(int argc, char** argv)
{
    if (argc != 3) {
        std::cerr << "usage: matcher FILE WORD\n";
        return 2;
    }
    std::ifstream in(argv[1]);
    std::string line;
    std::size_t total = 0;
    while (std::getline(in, line))
        total += count_matches(line, argv[2]);
    std::cout << total << '\n';
    return 0;
}
