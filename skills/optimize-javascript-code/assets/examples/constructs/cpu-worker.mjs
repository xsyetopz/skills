// Worker entry for hashInWorker in async.mjs: same loop, off the main thread.
import { parentPort, workerData } from "node:worker_threads";
import { hashBlocking } from "./async.mjs";

parentPort.postMessage(hashBlocking(workerData));
