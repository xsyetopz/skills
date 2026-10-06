# Ruby

Visibility is `public`, `protected`, and `private`,
set by a keyword that applies to the methods below it.
Never define a bare `def` at the top level of a file for a helper:
it becomes a private method on `Object` and leaks into every class.
Put constants and helpers inside a module or class namespace.

## Order in a file

1. Magic comment (`# frozen_string_literal: true`).
1. `require` and `require_relative`.
1. Namespace `module`, then the class.
1. Inside the class: mixins (`include`, `extend`), constants, `private_constant`, class methods,
   `initialize`, public methods, `protected` methods, `private` methods.
1. Private helpers last, inside the class or module that uses them.

Tests go in `test/` (Minitest) or `spec/` (RSpec), mirroring `lib/`.
Do not widen a method to `public` so a test can call it; test through the public methods.

```ruby
# frozen_string_literal: true

require "dependency"

module Project
  class PublicType
    PUBLIC_CONSTANT = 1
    PRIVATE_CONSTANT = 2
    private_constant :PRIVATE_CONSTANT

    def initialize
      @state = PRIVATE_CONSTANT
    end

    def public_method
      private_method
    end

    protected

    def protected_method
      @state
    end

    private

    def private_method
      @state + 1
    end
  end
end
```
