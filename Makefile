CC = gcc
CFLAGS = -O2 -Wall -Wextra -std=c11 -D_POSIX_C_SOURCE=200809L -pthread
LDFLAGS = -pthread
LDLIBS = -lm

TARGETS = pi_single pi_local pi_false_sharing pi_mutex pi_precise

all: $(TARGETS)

pi_single: pi_single.c
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

pi_local: pi_local.c common.h
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

pi_false_sharing: pi_false_sharing.c common.h
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

pi_mutex: pi_mutex.c
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

pi_precise: pi_precise.c common.h
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS) $(LDLIBS)

# Special builds from pi_mutex.c
pi_mutex_race: pi_mutex.c
	$(CC) $(CFLAGS) -DNO_MUTEX $< -o $@ $(LDFLAGS)

pi_mutex_local: pi_mutex.c
	$(CC) $(CFLAGS) -DLOCAL_ACCUMULATION $< -o $@ $(LDFLAGS)

pi_mutex_serial: pi_mutex.c
	$(CC) $(CFLAGS) -DSERIAL_BASELINE $< -o $@ $(LDFLAGS)

check: all
	chmod +x scripts/check.sh
	./scripts/check.sh

clean:
	rm -f $(TARGETS) pi_mutex_race pi_mutex_local pi_mutex_serial

rebuild: clean all

version:
	$(CC) --version

help:
	@echo "make              Build all programs"
	@echo "make check        Build and run correctness tests"
	@echo "make clean        Remove executables"
	@echo "make rebuild      Clean and rebuild"
	@echo "make pi_mutex_race   Build deliberate race demo"
	@echo "make pi_mutex_local  Build local accumulation reference"
	@echo "make pi_mutex_serial Build serial reference"

.PHONY: all check clean rebuild version help
