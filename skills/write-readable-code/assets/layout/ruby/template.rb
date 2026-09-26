# frozen_string_literal: true

require "json"

module Component
  PUBLIC_CONSTANT = 1
  PRIVATE_CONSTANT = 2
  private_constant :PRIVATE_CONSTANT

  class PublicType
    def initialize
      @state = PRIVATE_CONSTANT
    end

    def public_method
      JSON.generate(state: private_method)
    end

    protected

    def protected_method
      @state
    end

    private

    def private_method
      Component.send(:private_helper, protected_method)
    end
  end

  def self.private_helper(value)
    value * PUBLIC_CONSTANT
  end
  private_class_method :private_helper
end
