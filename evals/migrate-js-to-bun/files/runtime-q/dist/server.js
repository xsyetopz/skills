import { createServer } from "node:http";

const port = Number(process.env.PORT ?? 8080);
createServer((_req, res) => res.end("ok\n")).listen(port, () => console.log(`listening on ${port}`));
