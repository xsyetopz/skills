import { Repo } from "./repo.js";
import { Role } from "./roles.js";

export class AccessService {
	constructor(private readonly repo: Repo) {}

	canRefund(id: number): boolean {
		const user = this.repo.find(id);
		return user !== undefined && user.role === Role.Admin;
	}
}
