/* Doi chung false sharing cho Approach 2 (TV2).
 * Cach chay: ./pi_false_sharing <N> <T> <seed> <packed|padded>
 *   packed: counts[i] nam sat nhau (8 byte/phan tu) -> nhieu luong chung 1 cache line
 *   padded: moi bo dem chiem rieng 1 cache line 64 byte
 * Ca hai deu ghi vao mang chung TRONG vong lap (khac pi_local.c chi ghi 1 lan cuoi). */
#include "common.h"
#include <pthread.h>
#include <string.h>

typedef struct { volatile long long v; } packed_t;                 /* 8 byte  */
typedef struct { volatile long long v; char pad[56]; } padded_t;   /* 64 byte */

static packed_t *pk;
static padded_t *pd;
static int use_pad;

typedef struct { int id; long long n_points; unsigned int seed; } task_t;

static void *worker(void *arg) {
    task_t *t = (task_t *)arg;
    unsigned int seed = t->seed;
    volatile long long *c = use_pad ? &pd[t->id].v : &pk[t->id].v;
    for (long long i = 0; i < t->n_points; i++)
        if (sample_hit(&seed)) (*c)++;          /* ghi vao bo nho chung moi lan trung */
    return NULL;
}

int main(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "Usage: %s <N> <T> <seed> <packed|padded>\n", argv[0]); return 1; }
    long long n = atoll(argv[1]);
    int T = atoi(argv[2]);
    unsigned int base = (unsigned int)atoi(argv[3]);
    use_pad = strcmp(argv[4], "padded") == 0;

    pk = aligned_alloc(64, ((sizeof(packed_t) * T + 63) / 64) * 64);
    pd = aligned_alloc(64, sizeof(padded_t) * T);
    pthread_t *th = malloc(sizeof(pthread_t) * T);
    task_t *tk = malloc(sizeof(task_t) * T);
    for (int i = 0; i < T; i++) {
        pk[i].v = 0; pd[i].v = 0;
        tk[i].id = i;
        tk[i].n_points = n / T + (i == T - 1 ? n % T : 0);
        tk[i].seed = base + i;
    }

    double t0 = now_sec();
    for (int i = 0; i < T; i++) pthread_create(&th[i], NULL, worker, &tk[i]);
    long long hits = 0;
    for (int i = 0; i < T; i++) {
        pthread_join(th[i], NULL);
        hits += use_pad ? pd[i].v : pk[i].v;
    }
    double t1 = now_sec();

    print_csv(use_pad ? "fs_padded" : "fs_packed", T, n, 0, 4.0 * hits / n, t1 - t0);
    free(pk); free(pd); free(th); free(tk);
    return 0;
}
