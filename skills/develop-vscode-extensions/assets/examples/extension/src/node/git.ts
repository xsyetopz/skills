// Node-only: child_process is unavailable in the web extension host.
import { execFile } from "node:child_process";

/** Runs `<gitPath> config user.name` in cwd; undefined on failure. */
export function gitUserName(
	gitPath: string,
	cwd: string,
): Promise<string | undefined> {
	return new Promise((resolve) => {
		execFile(
			gitPath,
			["config", "user.name"],
			{ cwd, timeout: 5000 },
			(error, stdout) => {
				const name = String(stdout).trim();
				resolve(error || name === "" ? undefined : name);
			},
		);
	});
}
