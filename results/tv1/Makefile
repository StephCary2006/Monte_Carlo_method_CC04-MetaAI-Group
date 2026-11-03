CC     := gcc
CFLAGS := -Wall -Wextra -O2
TARGET := pi_single

.PHONY: all clean

all: $(TARGET)

$(TARGET): pi_single.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f $(TARGET)
