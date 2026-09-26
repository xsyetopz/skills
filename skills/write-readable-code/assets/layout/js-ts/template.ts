import { dependency } from "./dependency.js"; // stubbed by verify.sh

export const PUBLIC_CONSTANT = 1;
const PRIVATE_CONSTANT = 2;

export class PublicType {
	#state = 0;

	constructor() {}

	publicMethod(): void {}

	#privateMethod(): void {}
}

class PrivateType {
	#helper(): void {}
}

function privateHelper(): void {}

export function publicFunction(): void {}
