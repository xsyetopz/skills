package strutil

import "strings"

func Trim_Spaces(s string) string {
	return strings.TrimSpace(s)
}

func Get_Initials(name string) string {
	var b strings.Builder
	for _, w := range strings.Fields(name) {
		b.WriteString(strings.ToUpper(w[:1]))
	}
	return b.String()
}

func Join_With_Comma(parts []string) string {
	return strings.Join(parts, ", ")
}
