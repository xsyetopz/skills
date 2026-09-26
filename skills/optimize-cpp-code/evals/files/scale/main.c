#include "scale.h"

#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    size_t n = 1u << 20;
    float *a = malloc(n * sizeof *a), *b = malloc(n * sizeof *b);
    if (a == NULL || b == NULL)
        return 1;
    for (size_t i = 0; i < n; i++)
        b[i] = (float)(i % 1000) * 0.25f;
    double sum = 0;
    for (int rep = 0; rep < 200; rep++) {
        scale(a, b, n);
        sum += a[rep * 17 % n];
    }
    printf("%.2f %.2f\n", sum, (double)a[n - 1]);
    free(a);
    free(b);
    return 0;
}
