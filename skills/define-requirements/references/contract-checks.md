# Turn software requests into observable behavior contracts

For each noun, identify the actual entity and its lifetime. “File” can mean
path, open descriptor, current inode, uploaded object, or published version;
these do not have interchangeable identity. For each verb, identify when it
takes effect and who can observe it. “Save” does not establish flush, durable
commit, replication, or visibility to another client unless those observations
are specified.

Use units and domains explicitly: bytes versus characters; UTC timestamp versus
local date; inclusive versus exclusive endpoint; ordered sequence versus set;
empty versus absent; exact value versus tolerance; owned versus borrowed handle.
A hash identifies content only under the stated encoding and normalization.

For retries, write down what repeats. Repeating an HTTP request can repeat a
business operation unless the service's actual contract prevents it. Do not add
an idempotency-key protocol to a system that does not require one. For
concurrency, identify the state transition that arbitrates competing operations;
wall-clock arrival order is not automatically a serialization order.

An acceptance example needs preconditions, one event or controlled interleaving,
and externally distinguishable observations. A mocked call count is enough only
when that interaction itself is the contract. “No errors were logged” does not
show that work was completed. “Returns 200” does not establish data correctness.

Trace each mandatory requirement to supplied intent, an existing public
contract, or a disclosed decision. Put guesses beside the requirement they
affect. Do not turn your preferred implementation into a user's requirement.

Use the worked asset to see an explicit cancellation/publication race. Its
domain choices are examples; preserve the actual request's choices when they
differ.
