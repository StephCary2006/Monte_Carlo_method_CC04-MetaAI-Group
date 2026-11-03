/* Approach 3 - Shared Variable + Mutex.
 * Cach chay: ./pi_mutex <N> <T> <seed> [k]
 *   k = 1 (mac dinh): moi diem trung -> lock, global_hits++, unlock
 *   k > 1 (thi nghiem 6.1): dem cuc bo, cu sau k vong lap moi lock va cong don */
#include "common.h"
#include <pthread.h>

static long long global_hits = 0;                       /* BIEN CHUNG */
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

typedef struct { long long n_points; unsigned int seed; int k; } task_t;

static void *worker(void *arg) {
    task_t *t = (task_t *)arg;
    unsigned int seed = t->seed;
    if (t->k <= 1) {
        for (long long i = 0; i < t->n_points; i++) {
            if (sample_hit(&seed)) {
                pthread_mutex_lock(&lock);              /* critical section */
                global_hits++;
                pthread_mutex_unlock(&lock);
            }
        }
    } else {
        long long pending = 0;
        for (long long i = 0; i < t->n_points; i++) {
            pending += sample_hit(&seed);
            if ((i + 1) % t->k == 0) {                  /* dong bo moi k vong */
                pthread_mutex_lock(&lock);
                global_hits += pending;
                pthread_mutex_unlock(&lock);
                pending = 0;
            }
        }
        pthread_mutex_lock(&lock);                      /* phan con lai */
        global_hits += pending;
        pthread_mutex_unlock(&lock);
    }
    return NULL;
}

int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "Usage: %s <N> <T> <seed> [k]\n", argv[0]); return 1; }
    long long n = atoll(argv[1]);
    int T = atoi(argv[2]);
    unsigned int base = (unsigned int)atoi(argv[3]);
    int k = (argc >= 5) ? atoi(argv[4]) : 1;

    pthread_t *th = malloc(sizeof(pthread_t) * T);
    task_t *tk = malloc(sizeof(task_t) * T);
    for (int i = 0; i < T; i++) {
        tk[i].n_points = n / T + (i == T - 1 ? n % T : 0);
        tk[i].seed = base + i;
        tk[i].k = k;
    }

    double t0 = now_sec();
    for (int i = 0; i < T; i++) pthread_create(&th[i], NULL, worker, &tk[i]);
    for (int i = 0; i < T; i++) pthread_join(th[i], NULL);
    double t1 = now_sec();

    print_csv("mutex", T, n, k, 4.0 * global_hits / n, t1 - t0);
    pthread_mutex_destroy(&lock);
    free(th); free(tk);
    return 0;
}
