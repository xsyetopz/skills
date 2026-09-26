# Paylane webhook delivery (excerpt from the provider's integration guide)

- Delivery is at least once. The same event can arrive more than once, for
  example when your endpoint times out or returns a non-2xx status.
- Every event has an `id` field (for example `evt_3KfA9`) that stays the
  same across all deliveries of that event.
- Failed deliveries are retried with backoff for up to 72 hours.
- Events are not guaranteed to arrive in order.
