((rule
  (targets) @name) @item
  (#not-match? @name "^\\."))

(variable_assignment
  name: (word) @name) @item

(define_directive
  "define" @context
  name: (word) @name) @item
