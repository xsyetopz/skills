/* Each faulty branch remains defined C behavior but violates its contract. */
#include <limits.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static bool contract(bool bad, int topic) {
    switch (topic) {
    case 1: { /* Reject a sum that cannot fit, rather than report wrapped success. */
        unsigned a = UINT_MAX, b = 1;
        bool accepted = bad ? true : b <= UINT_MAX - a;
        return !accepted;
    }
    case 2: { /* Copy object representation, not a numeric conversion. */
        uint32_t input = UINT32_C(0x3f800000);
        unsigned char bytes[sizeof input];
        if (bad) memset(bytes, (unsigned char)input, sizeof bytes);
        else memcpy(bytes, &input, sizeof bytes);
        uint32_t output;
        memcpy(&output, bytes, sizeof output);
        return output == input;
    }
    case 3: { /* Overlap: moving abc one byte right produces aabc. */
        char value[] = "abcd";
        if (bad) { for (size_t i = 0; i < 3; ++i) value[i + 1] = value[i]; }
        else memmove(value + 1, value, 3);
        return memcmp(value, "aabc", 4) == 0;
    }
    case 4: { /* A handle denotes an ID, not a compacted slot. */
        int ids[] = {10, 20, 30};
        int handle = bad ? 1 : 20;
        memmove(ids, ids + 1, 2 * sizeof ids[0]);
        int found = -1;
        if (bad) found = ids[handle];
        else for (size_t i = 0; i < 2; ++i) if (ids[i] == handle) found = ids[i];
        return found == 20;
    }
    case 5: { /* A required snapshot must not observe later caller writes. */
        char input[] = "old", copy[sizeof input];
        memcpy(copy, input, sizeof copy);
        const char *snapshot = bad ? input : copy;
        input[0] = 'n';
        return strcmp(snapshot, "old") == 0;
    }
    case 6: { /* Remove every matching element, including adjacent matches. */
        int values[] = {2, 4, 5};
        size_t size = 3, i = 0;
        while (i < size) {
            if (values[i] % 2 == 0) {
                memmove(values + i, values + i + 1, (size - i - 1) * sizeof values[0]);
                --size;
                if (bad) ++i;
            } else ++i;
        }
        return size == 1 && values[0] == 5;
    }
    case 7: { /* An embedded NUL is data in a length-delimited byte buffer. */
        const unsigned char bytes[] = {'a', 0, 'b'};
        size_t observed = bad ? strlen((const char *)"a\0b") : sizeof bytes;
        return observed == 3;
    }
    case 8: { /* A snapshot preserves a floating value's signed zero. */
        double input = -0.0;
        double output = bad ? fabs(input) : input;
        return output == 0.0 && signbit(output);
    }
    default: fputs("topic must be 1..8\n", stderr); exit(2);
    }
}
int main(int argc, char **argv) {
    if (argc != 3 || (strcmp(argv[1], "red") && strcmp(argv[1], "green")) ||
        strlen(argv[2]) != 1 || argv[2][0] < '1' || argv[2][0] > '8') {
        fputs("usage: semantics red|green TOPIC(1..8)\n", stderr); return 2;
    }
    int topic = argv[2][0] - '0';
    bool pass = contract(strcmp(argv[1], "red") == 0, topic);
    printf("CONTRACT topic %d: %s\n", topic, pass ? "PASS" : "FAIL");
    return pass ? 0 : 1;
}
