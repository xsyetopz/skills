package main
import "fmt"
func main() {
	owner := make([]int, 1, 2)
	owner[0] = 1
	view := append(owner, 2)
	owner = append(owner, 3)
	fmt.Printf("actual view=%v expected independent [1 2]\n", view)
	if view[1] != 3 { panic("alias not reproduced") }
}
