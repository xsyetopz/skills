package component

import (
	"fmt"
)

const PublicConstant = 1
const privateConstant = 2

var PublicVariable = 1
var privateVariable = 2

type PublicType struct {
	PublicField  int
	privateField int
}

func NewPublicType() *PublicType {
	return &PublicType{}
}

func (p *PublicType) PublicMethod() {
}

func (p *PublicType) privateMethod() {
}

type privateType struct {
	value int
}

func privateHelper() {
	fmt.Print("")
}
