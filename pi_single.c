#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#define DEFAULT_POINTS 10000000ULL
#define DEFAULT_SEED   12345ULL

static uint64_t next_rand(uint64_t *state)
{
    uint64_t z = (*state += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

static double next_unit(uint64_t *state)
{
    return (next_rand(state) >> 11) * (1.0 / 9007199254740992.0);
}

static uint64_t count_inside(uint64_t n, uint64_t seed)
{
    uint64_t state = seed, inside = 0, i;
    for (i = 0; i < n; i++) {
        double x = next_unit(&state);
        double y = next_unit(&state);

        if (x * x + y * y <= 1.0)
            inside++;
    }
    return inside;
}

static int parse_ull(const char *s, unsigned long long *out)
{
    char *end;
    if (s[0] < '0' || s[0] > '9')
        return -1;
    errno = 0;
    *out = strtoull(s, &end, 10);
    return (*end != '\0' || errno != 0) ? -1 : 0;
}

int main(int argc, char *argv[])
{
    unsigned long long n = DEFAULT_POINTS, seed = DEFAULT_SEED;
    uint64_t inside;
    double pi, err, elapsed;
    struct timespec t0, t1;

    if (argc > 3 || (argc >= 2 && (parse_ull(argv[1], &n) != 0 || n == 0))
        || (argc == 3 && parse_ull(argv[2], &seed) != 0)) {
        fprintf(stderr, "Usage: %s [num-points] [seed]\n", argv[0]);
        return 1;
    }

    clock_gettime(CLOCK_MONOTONIC, &t0);
    inside = count_inside(n, seed);
    clock_gettime(CLOCK_MONOTONIC, &t1);

    pi = 4.0 * (double)inside / (double)n;
    err = pi > 3.14159265358979323846 ? pi - 3.14159265358979323846
                                      : 3.14159265358979323846 - pi;
    elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;

    printf("Points      : %llu\n", n);
    printf("Seed        : %llu\n", seed);
    printf("Inside      : %llu\n", (unsigned long long)inside);
    printf("Pi estimate : %.8f\n", pi);
    printf("Abs error   : %.8f\n", err);
    printf("Time: %.6f s\n", elapsed);
    return 0;
}