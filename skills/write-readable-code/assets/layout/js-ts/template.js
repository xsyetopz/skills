import { dependency } from "./dependency.js"; // stubbed by verify.sh

export const PUBLIC_CONSTANT = 1;
const PRIVATE_CONSTANT = 2;

export class PublicType {
	#state = 0;

	constructor() {}

	publicMethod() {}

	#privateMethod() {}
}

class PrivateType {
	#helper() {}
}

function privateHelper() {}

export function publicFunction() {}
