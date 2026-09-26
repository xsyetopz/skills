CC ?= cc
CFLAGS ?= -O2 -Wall
OBJS = src/main.o src/util.o

app: $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS)

src/%.o: src/%.c src/util.h
	$(CC) $(CFLAGS) -c -o $@ $<

.PHONY: clean
clean:
	rm -f app $(OBJS)
