#include "scale.h"

void scale(float *a, const float *b, size_t n)
{
    for (size_t i = 0; i < n; i++)
        a[i] = b[i] * 2.0f;
}
