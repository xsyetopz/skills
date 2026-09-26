// Must NOT type-check: arguments are swapped. verify.sh expects TS2345.
import { membershipKey, tenantId, userId } from "./ids";

export const wrong = membershipKey(tenantId(3), userId(7));
