import { route, shouldLog } from "./filter.js";
import { Level } from "./levels.js";

const lines = [Level.Debug, Level.Info, Level.Warn, Level.Error].map(
	(level) => `${Level[level]} ${shouldLog(level, Level.Info)} ${route(level)}`,
);
console.log(lines.join("\n"));
