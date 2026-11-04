/* Approach 1 - Single Thread (baseline). Cach chay: ./pi_single <N> <seed> */
#include "common.h"

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "Usage: %s <N> <seed>\n", argv[0]); return 1; }
    long long n = atoll(argv[1]);
    unsigned int seed = (unsigned int)atoi(argv[2]);

    double t0 = now_sec();                 /* bat dau do */
    long long hits = 0;
    for (long long i = 0; i < n; i++)
        hits += sample_hit(&seed);         /* KHONG printf trong vong lap */
    double t1 = now_sec();                 /* ket thuc do */

    print_csv("single", 1, n, 0, 4.0 * hits / n, t1 - t0);
    return 0;
}
