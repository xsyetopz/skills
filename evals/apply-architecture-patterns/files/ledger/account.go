package ledger

import "errors"

const maxBalanceCents = 100_000_000

var ErrInsufficient = errors.New("ledger: insufficient funds")

type Account struct {
	ID           string
	balanceCents int64
}

func NewAccount(id string, balanceCents int64) *Account {
	return &Account{ID: id, balanceCents: balanceCents}
}

func (a *Account) Balance() int64 {
	return a.balanceCents
}

func (a *Account) withdraw(cents int64) error {
	if cents > a.balanceCents {
		return ErrInsufficient
	}
	a.balanceCents -= cents
	return nil
}

func (a *Account) deposit(cents int64) {
	a.balanceCents = min(a.balanceCents+cents, maxBalanceCents)
}
