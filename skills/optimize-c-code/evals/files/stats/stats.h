#ifndef STATS_H
#define STATS_H
double mean(const double *values,int count);
double variance(const double*values, int n);
int count_above(const double *values, int n, double limit);
int record(double value);
#endif
