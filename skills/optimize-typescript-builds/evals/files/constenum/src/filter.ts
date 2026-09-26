import { Channel, Level } from "./levels.js";

export function shouldLog(level: Level, min: Level): boolean {
	return level >= min;
}

export function route(level: Level): Channel {
	return level >= Level.Warn ? Channel.File : Channel.Console;
}
