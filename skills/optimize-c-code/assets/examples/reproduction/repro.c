/* Reproduce truncation when text length is used for a binary payload. */
#include <stdio.h>
#include <string.h>
int main(void) {
    const unsigned char actual[] = {97, 0, 98, 0};
    size_t observed = strlen((const char *)actual);
    if (observed != 1 || sizeof actual - 1 != 3) return 1;
    puts("REPRODUCED: text length 1 truncates the required 3-byte binary payload");
    return 0;
}
