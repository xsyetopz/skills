// Package encoder renders log records for the shipper's wire format.
package encoder

import "fmt"

// Field is one key/value pair of a log record.
type Field struct {
	Key string
	Val int64
}

// Encode renders fields as "key=value " pairs in input order.
func Encode(fields []Field) string {
	out := ""
	for _, f := range fields {
		out += fmt.Sprintf("%s=%d ", f.Key, f.Val)
	}
	return out
}
