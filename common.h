/* common.h - tien ich dung chung cho ca 3 approach (TV1 phu trach) */
#ifndef COMMON_H
#define COMMON_H

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

/* Thoi gian thuc (wall-clock) tinh bang giay.
 * Dung CLOCK_MONOTONIC, KHONG dung clock() vi clock() cong don CPU time cua moi luong. */
static inline double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

/* Sinh 1 diem ngau nhien trong [-1,1]x[-1,1], tra ve 1 neu nam trong hinh tron.
 * rand_r() chi dung state cua chinh luong goi -> khong co khoa an nhu rand(). */
static inline int sample_hit(unsigned int *seed) {
    double x = 2.0 * rand_r(seed) / RAND_MAX - 1.0;
    double y = 2.0 * rand_r(seed) / RAND_MAX - 1.0;
    return (x * x + y * y) <= 1.0;
}

/* In dung 1 dong CSV: approach,threads,n_points,k,pi_estimate,time_sec */
static inline void print_csv(const char *approach, int threads, long long n,
                             int k, double pi, double t) {
    printf("%s,%d,%lld,%d,%.6f,%.6f\n", approach, threads, n, k, pi, t);
}

#endif
