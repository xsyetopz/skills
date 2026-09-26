((rule
  (targets
    (word) @run @make_target))
  (#not-match? @make_target "^\\.")
  (#set! tag make-target))
