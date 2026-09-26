#include <stdio.h>
#include "stats.h"

int main(void)
{
    double xs[] = {2, 4, 4, 4, 5, 5, 7, 9};
    int n = (int)(sizeof xs / sizeof xs[0]);
    for (int i = 0; i < n; i++) record(xs[i]);
    printf("mean=%.3f variance=%.3f above4=%d records=%d\n", mean(xs, n), variance(xs, n),
           count_above(xs, n, 4), record(0));
    return 0;
}
