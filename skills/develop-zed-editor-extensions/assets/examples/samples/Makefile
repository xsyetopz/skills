# Build the demo program.
CC ?= cc
CFLAGS := -O2 -g
SRC := $(wildcard *.c)

define greet
@echo "hello $(1)"
endef

ifeq ($(CC),cc)
LD := $(CC)
endif

.PHONY: all clean

all: build/app

build/app: $(SRC)
	mkdir -p $(@D)
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -rf build
