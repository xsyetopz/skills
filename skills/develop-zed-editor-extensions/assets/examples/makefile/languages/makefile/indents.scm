(rule
  (recipe) @indent)

(define_directive
  "define" @start
  "endef" @end) @indent

(conditional
  "endif" @end) @indent
