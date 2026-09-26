// Package surface shows one obvious way to build a Config: a single
// exported constructor. Helpers stay unexported until a caller needs them.
package surface

import (
	"errors"
	"strings"
)

// Config is a parsed key=value configuration.
type Config struct {
	values map[string]string
}

// Parse is the only exported way to create a Config.
func Parse(text string) (Config, error) {
	values := map[string]string{}
	for _, line := range strings.Split(text, "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		key, value, ok := strings.Cut(line, "=")
		if !ok {
			return Config{}, errors.New("missing '=' in " + line)
		}
		values[normalize(key)] = strings.TrimSpace(value)
	}
	return Config{values: values}, nil
}

// Get returns the value for key and whether it was present.
func (c Config) Get(key string) (string, bool) {
	value, ok := c.values[normalize(key)]
	return value, ok
}

func normalize(key string) string {
	return strings.ToLower(strings.TrimSpace(key))
}
