/* Approach 2 - Multi-thread, Local Accumulation (map-reduce).
 * Cach chay: ./pi_local <N> <T> <seed> */
#include "common.h"
#include <pthread.h>

typedef struct {
    long long n_points;     /* so diem luong nay xu ly        */
    unsigned int seed;      /* seed rieng cua luong           */
    long long hits;         /* ket qua - chi ghi 1 lan cuoi   */
} task_t;

static void *worker(void *arg) {
    task_t *t = (task_t *)arg;
    unsigned int seed = t->seed;           /* copy ra bien cuc bo */
    long long local = 0;                   /* dem cuc bo tren stack */
    for (long long i = 0; i < t->n_points; i++)
        local += sample_hit(&seed);
    t->hits = local;                       /* MAP xong: ghi 1 lan duy nhat */
    return NULL;
}

int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "Usage: %s <N> <T> <seed>\n", argv[0]); return 1; }
    long long n = atoll(argv[1]);
    int T = atoi(argv[2]);
    unsigned int base = (unsigned int)atoi(argv[3]);

    pthread_t *th = malloc(sizeof(pthread_t) * T);   /* cap phat ngoai vung do */
    task_t *tk = malloc(sizeof(task_t) * T);
    for (int i = 0; i < T; i++) {
        tk[i].n_points = n / T + (i == T - 1 ? n % T : 0);   /* luong cuoi nhan phan du */
        tk[i].seed = base + i;
        tk[i].hits = 0;
    }

    double t0 = now_sec();
    for (int i = 0; i < T; i++) pthread_create(&th[i], NULL, worker, &tk[i]);
    long long hits = 0;
    for (int i = 0; i < T; i++) { pthread_join(th[i], NULL); hits += tk[i].hits; }  /* REDUCE */
    double t1 = now_sec();

    print_csv("local", T, n, 0, 4.0 * hits / n, t1 - t0);
    free(th); free(tk);
    return 0;
}
