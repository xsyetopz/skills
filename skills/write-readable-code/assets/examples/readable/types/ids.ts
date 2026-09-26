// Branded identifier and unit types. Check with: tsc --noEmit --strict ids.ts
declare const brand: unique symbol;
type Brand<T, Name extends string> = T & { readonly [brand]: Name };

export type UserId = Brand<number, "UserId">;
export type TenantId = Brand<number, "TenantId">;
export type Milliseconds = Brand<number, "Milliseconds">;

export const userId = (value: number): UserId => value as UserId;
export const tenantId = (value: number): TenantId => value as TenantId;
export const ms = (value: number): Milliseconds => value as Milliseconds;

export function membershipKey(user: UserId, tenant: TenantId): string {
	return `${tenant}:${user}`;
}

export function deadline(start: Milliseconds, timeout: Milliseconds) {
	return ms(start + timeout);
}
