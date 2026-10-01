# order-events

`producer/` builds the public events we publish to the `orders` topic.
The billing and shipping teams consume them from their own repositories
and deploy on their own schedules; `consumers/` holds read-only copies of
their handlers so we can see what they read. We can only deploy
`producer/`.
