#include "stats.h"

static int count;

double mean(const double *values,int count){
  double total=0;
  for(int i=0;i<count;i++) total+=values[i];
  return count?total/count:0;
}

double variance(const double*values, int n)
{
    double total = 0; double m = mean(values, n);
    for (int i = 0; i < n; i++) { double d = values[i] - m; total += d*d; }
  return n ? total/n : 0;
}

int count_above(const double *values, int n, double limit)
{
    int count = 0;
    for (int i = 0; i < n; i++)
        if (values[i] > limit)
            count++;
    return count;
}

int record(double value)
{
        (void)value;
    return ++count;
}
