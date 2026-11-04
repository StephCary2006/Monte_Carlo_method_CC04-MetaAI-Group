/*
 * Monte Carlo pi: Approach 3, a shared counter protected by a mutex.
 * Usage: ./pi_mutex <points> <threads> [k=1] [seed=42]
 *
 * Optional builds from this SAME source for controlled comparisons:
 *   -DNO_MUTEX           Deliberate data race; demonstration only.
 *   -DLOCAL_ACCUMULATION Approach 2 reference, no shared updates in the loop.
 *   -DSERIAL_BASELINE    Direct serial reference (requires threads=1).
 */
#define _POSIX_C_SOURCE 200809L
#include <ctype.h>
#include <errno.h>
#include <inttypes.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef SERIAL_BASELINE
#define LOCAL_ACCUMULATION
#endif
#if defined(NO_MUTEX) && defined(LOCAL_ACCUMULATION)
#error "Choose either NO_MUTEX or LOCAL_ACCUMULATION, not both"
#endif

#define GAMMA UINT64_C(0x9e3779b97f4a7c15)
static uint64_t global_hits = 0;
#if !defined(NO_MUTEX) && !defined(LOCAL_ACCUMULATION)
static pthread_mutex_t hits_mutex;
#endif

struct worker_args {
    uint64_t first;       /* Index of the first point assigned to this worker. */
    uint64_t count;
    uint64_t k;
    uint64_t seed;
    uint64_t local_hits;  /* Reference result, written once at thread exit. */
};

#ifndef SERIAL_BASELINE
static void check_pthread(int error, const char *operation)
{
    if (error != 0) {
        fprintf(stderr, "%s: %s\n", operation, strerror(error));
        exit(EXIT_FAILURE);
    }
}
#endif

/* SplitMix64 mixing steps from Sebastiano Vigna's public-domain implementation:
 * https://prng.di.unimi.it/splitmix64.c
 * State is LOCAL to each worker, never shared between threads.
 * Unsigned wraparound is intentional in this generator.
 */
static uint64_t next_random(uint64_t *state)
{
    uint64_t z = (*state += GAMMA);
    z = (z ^ (z >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94d049bb133111eb);
    return z ^ (z >> 31);
}

static double coordinate(uint64_t *state)
{
    /* 53 random bits -> [0,1), then scale to [-1,1). */
    return 2.0 * (double)(next_random(state) >> 11) * 0x1.0p-53 - 1.0;
}

#ifndef LOCAL_ACCUMULATION
static void publish_batch(uint64_t hits)
{
#ifndef NO_MUTEX
    check_pthread(pthread_mutex_lock(&hits_mutex), "pthread_mutex_lock");
#endif
    global_hits += hits;  /* The ONLY shared update in the computation. */
#ifndef NO_MUTEX
    check_pthread(pthread_mutex_unlock(&hits_mutex), "pthread_mutex_unlock");
#endif
}
#endif

static void *sample_points(void *argument)
{
    struct worker_args *args = argument;
    const uint64_t count = args->count;
    /* Two RNG draws per point. Workers use disjoint parts of the same stream,
     * so the point set stays identical when threads or k change.
     */
    uint64_t state = args->seed + UINT64_C(2) * args->first * GAMMA;
#ifndef LOCAL_ACCUMULATION
    const uint64_t k = args->k;
    uint64_t batch_hits = 0, batch_points = 0;
#endif
#if defined(LOCAL_ACCUMULATION) || defined(NO_MUTEX)
    uint64_t local_hits = 0;
#endif

    for (uint64_t i = 0; i < count; ++i) {
        double x = coordinate(&state);
        double y = coordinate(&state);
        uint64_t hit = (x * x + y * y <= 1.0) ? 1 : 0;
#if defined(LOCAL_ACCUMULATION) || defined(NO_MUTEX)
        local_hits += hit;
#endif
#ifndef LOCAL_ACCUMULATION
        batch_hits += hit;
        ++batch_points;
        if (batch_points == k) {
            /* Publish even if batch_hits=0: k counts POINTS, not only hits. */
            publish_batch(batch_hits);
            batch_hits = 0;
            batch_points = 0;
        }
#endif
    }
#ifndef LOCAL_ACCUMULATION
    /* A final incomplete batch must not be lost. Empty workers publish none. */
    if (batch_points != 0)
        publish_batch(batch_hits);
#endif
#if defined(LOCAL_ACCUMULATION) || defined(NO_MUTEX)
    args->local_hits = local_hits;
#endif
    return NULL;
}

static uint64_t parse_u64(const char *text, const char *name)
{
    char *end;
    uintmax_t value;
    if (*text == '\0') {
        fprintf(stderr, "%s cannot be empty\n", name);
        exit(EXIT_FAILURE);
    }
    for (const char *p = text; *p; ++p) {
        if (!isdigit((unsigned char)*p)) {
            fprintf(stderr, "%s must be an unsigned decimal integer\n", name);
            exit(EXIT_FAILURE);
        }
    }
    errno = 0;
    value = strtoumax(text, &end, 10);
    if (errno == ERANGE || *end != '\0' || value > UINT64_MAX) {
        fprintf(stderr, "%s is too large\n", name);
        exit(EXIT_FAILURE);
    }
    return (uint64_t)value;
}

int main(int argc, char **argv)
{
    uint64_t points, requested, k, seed, first = 0, updates = 0;
    size_t threads;
    struct worker_args *args;
    struct timespec start, finish;
#ifndef SERIAL_BASELINE
    pthread_t *ids;
    size_t created = 0;
    int create_error = 0;
#endif

    if (argc < 3 || argc > 5) {
        fprintf(stderr, "Usage: %s <points> <threads> [k=1] [seed=42]\n", argv[0]);
        return EXIT_FAILURE;
    }
    points = parse_u64(argv[1], "points");
    requested = parse_u64(argv[2], "threads");
    k = argc >= 4 ? parse_u64(argv[3], "k") : 1;
    seed = argc >= 5 ? parse_u64(argv[4], "seed") : 42;
    if (points == 0 || points > UINT64_MAX / 2 || requested == 0 || k == 0 ||
        requested > SIZE_MAX / sizeof(*args) || requested > SIZE_MAX / sizeof(pthread_t)) {
        fprintf(stderr, "Require points in 1..2^63-1, threads > 0, k > 0, and feasible allocations.\n");
        return EXIT_FAILURE;
    }
#ifdef SERIAL_BASELINE
    if (requested != 1) {
        fprintf(stderr, "The serial reference requires threads=1.\n");
        return EXIT_FAILURE;
    }
#endif
    threads = (size_t)requested;
    args = calloc(threads, sizeof(*args));
    if (args == NULL) { perror("calloc"); return EXIT_FAILURE; }
#ifndef SERIAL_BASELINE
    ids = calloc(threads, sizeof(*ids));
    if (ids == NULL) { perror("calloc"); free(args); return EXIT_FAILURE; }
#endif
    for (size_t i = 0; i < threads; ++i) {
        args[i].first = first;
        args[i].count = points / requested + (i < points % requested ? 1 : 0);
        args[i].k = k;
        args[i].seed = seed;
        first += args[i].count;
        updates += args[i].count / k + (args[i].count % k != 0);
    }
#if !defined(NO_MUTEX) && !defined(LOCAL_ACCUMULATION)
    check_pthread(pthread_mutex_init(&hits_mutex, NULL), "pthread_mutex_init");
#endif
    /* Timing includes creation, computation, joins, and any final reduction.
     * Argument parsing, allocation, mutex init, and printing are excluded.
     */
    if (clock_gettime(CLOCK_MONOTONIC, &start) == -1) {
        perror("clock_gettime"); exit(EXIT_FAILURE);
    }
#ifdef SERIAL_BASELINE
    sample_points(&args[0]);
#else
    for (size_t i = 0; i < threads; ++i) {
        create_error = pthread_create(&ids[i], NULL, sample_points, &args[i]);
        if (create_error != 0) break;
        ++created;
    }
    for (size_t i = 0; i < created; ++i)
        check_pthread(pthread_join(ids[i], NULL), "pthread_join");
    /* Never report a pi estimate based on partially created workers. */
    check_pthread(create_error, "pthread_create");
#endif
#ifdef LOCAL_ACCUMULATION
    for (size_t i = 0; i < threads; ++i)
        global_hits += args[i].local_hits;
    updates = 0; /* No shared-counter publications by the workers. */
#endif
    if (clock_gettime(CLOCK_MONOTONIC, &finish) == -1) {
        perror("clock_gettime"); exit(EXIT_FAILURE);
    }
    double seconds = (double)(finish.tv_sec - start.tv_sec) +
                     (double)(finish.tv_nsec - start.tv_nsec) / 1e9;
#if !defined(NO_MUTEX) && !defined(LOCAL_ACCUMULATION)
    check_pthread(pthread_mutex_destroy(&hits_mutex), "pthread_mutex_destroy");
#endif

#ifdef NO_MUTEX
    puts("mode=race_demo");
    fprintf(stderr, "WARNING: deliberate data race (undefined behavior); exclude from timing results.\n");
#elif defined(SERIAL_BASELINE)
    puts("mode=serial");
#elif defined(LOCAL_ACCUMULATION)
    puts("mode=local");
#else
    puts("mode=mutex");
#endif
    printf("points=%" PRIu64 "\nthreads=%zu\nk=%" PRIu64 "\nseed=%" PRIu64 "\n",
           points, threads, k, seed);
    printf("inside=%" PRIu64 "\npi=%.12f\nseconds=%.9f\nupdates=%" PRIu64 "\n",
           global_hits, 4.0 * (double)global_hits / (double)points, seconds, updates);
#ifdef NO_MUTEX
    uint64_t expected = 0;
    for (size_t i = 0; i < threads; ++i) expected += args[i].local_hits;
    printf("reference_inside=%" PRIu64 "\nreference_pi=%.12f\ncounts_match=%s\n",
           expected, 4.0 * (double)expected / (double)points,
           expected == global_hits ? "yes" : "no");
#endif
#ifndef SERIAL_BASELINE
    free(ids);
#endif
    free(args);
    return EXIT_SUCCESS;
}
