(comment) @comment

(targets
  (word) @function)

(variable_assignment
  name: (word) @variable)

(define_directive
  name: (word) @variable)

(variable_reference
  (word) @variable.special)

(automatic_variable) @variable.special

(function_call) @function @function.builtin

(string) @string

[
  "="
  ":="
  "::="
  "?="
  "+="
] @operator

[
  "("
  ")"
  "{"
  "}"
] @punctuation.bracket

":" @punctuation.delimiter

[
  "include"
  "define"
  "endef"
  "ifeq"
  "ifneq"
  "ifdef"
  "ifndef"
  "else"
  "endif"
  "export"
] @keyword
