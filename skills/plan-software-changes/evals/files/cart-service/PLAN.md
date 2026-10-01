# Plan: add-to-cart endpoint

Goal: `POST /cart/items` adds one item to the signed-in user's cart.
Users often have the app open on a phone and a laptop at the same time.

## Tasks

- T1 [depends: -] [files: src/cart/api.py] Add the endpoint handler.
  Verify: `just test-cart`
  Done when: the handler returns 200.
- T2 [depends: T1] [files: cart/store.py] In the handler, read the cart
  with `read_cart`, append the item, and save it with `write_cart`.
  Verify: `just test`
  Done when: the item appears in the cart.
- T3 [depends: T2] [files: cart/store.py] Retry the whole handler up to
  three times on any Redis error.
  Verify: `just test`
  Done when: a transient Redis error no longer fails the request.
