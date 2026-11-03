/* pi_precise.c - Approach 2 (local accumulation) cho do CHINH XAC cao.
 * KHONG dung cho do hieu nang (bo do hieu nang van dung pi_local.c, N = 10^7).
 * Khac pi_local.c: dung bo sinh 64-bit xoshiro256** (chu ky 2^256 - 1) thay rand_r
 * (rand_r chi co state 32 bit -> lap lai sau toi da 2^32 lan goi, khong du cho N rat lon).
 * Cach chay: ./pi_precise <N> <T> <seed>      vi du: ./pi_precise 1000000000000 8 2024 */
#include "common.h"
#include <pthread.h>
#include <stdint.h>
#include <math.h>
#define PI_TRUE 3.14159265358979323846

typedef struct { uint64_t s[4]; } rng_t;

static inline uint64_t splitmix64(uint64_t *x) {          /* dung de khoi tao state */
    uint64_t z = (*x += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}
static inline uint64_t rotl(uint64_t x, int k) { return (x << k) | (x >> (64 - k)); }
static inline uint64_t xoshiro(rng_t *r) {                 /* xoshiro256** */
    uint64_t *s = r->s, res = rotl(s[1] * 5, 7) * 9, t = s[1] << 17;
    s[2] ^= s[0]; s[3] ^= s[1]; s[1] ^= s[2]; s[0] ^= s[3]; s[2] ^= t; s[3] = rotl(s[3], 45);
    return res;
}
static inline double u01(rng_t *r) { return (xoshiro(r) >> 11) * 0x1.0p-53; }  /* [0,1), 53 bit */

typedef struct { long long n_points; uint64_t seed; long long hits; } task_t;

static void *worker(void *arg) {
    task_t *t = (task_t *)arg;
    rng_t r; uint64_t sm = t->seed;
    for (int i = 0; i < 4; i++) r.s[i] = splitmix64(&sm);
    long long local = 0;
    for (long long i = 0; i < t->n_points; i++) {
        double x = u01(&r), y = u01(&r);
        local += (x * x + y * y) < 1.0;                    /* 1/4 hinh tron don vi */
    }
    t->hits = local;
    return NULL;
}

int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "Usage: %s <N> <T> <seed>\n", argv[0]); return 1; }
    long long n = atoll(argv[1]);
    int T = atoi(argv[2]);
    uint64_t base = (uint64_t)atoll(argv[3]);

    pthread_t *th = malloc(sizeof(pthread_t) * T);
    task_t *tk = malloc(sizeof(task_t) * T);
    for (int i = 0; i < T; i++) {
        tk[i].n_points = n / T + (i == T - 1 ? n % T : 0);
        tk[i].seed = base * 1000003ULL + (uint64_t)i;      /* luong khac nhau -> state khac nhau */
    }
    double t0 = now_sec();
    for (int i = 0; i < T; i++) pthread_create(&th[i], NULL, worker, &tk[i]);
    long long hits = 0;
    for (int i = 0; i < T; i++) { pthread_join(th[i], NULL); hits += tk[i].hits; }
    double t1 = now_sec();

    double pi = 4.0 * (double)hits / (double)n;
    double q = (double)hits / (double)n;
    double se = 4.0 * sqrt(q * (1 - q) / (double)n);       /* sai so chuan ly thuyet */
    double err = fabs(pi - PI_TRUE);
    int digits = 0;
    while (digits < 15 && floor(pi * pow(10, digits + 1)) == floor(PI_TRUE * pow(10, digits + 1))) digits++;
    printf("N = %lld, T = %d, seed = %llu, time = %.2f s\n", n, T, (unsigned long long)base, t1 - t0);
    printf("pi estimate = %.10f\n", pi);
    printf("true pi     = %.10f\n", PI_TRUE);
    printf("|error|     = %.2e   (std error = %.2e)\n", err, se);
    printf("correct decimals = %d\n", digits);
    free(th); free(tk);
    return 0;
}
