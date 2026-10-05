import { routes } from "./generated/routes";

export function hasRoute(path: string): boolean {
  return (routes as readonly string[]).includes(path);
}
