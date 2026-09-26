import express from 'express';

const app = express();
app.use(express.json());

app.get('/health', (_req, res) => res.json({ ok: true }));
app.post('/orders', (req, res) => {
  const items = Array.isArray(req.body?.items) ? req.body.items : [];
  res.status(201).json({ count: items.length });
});

const port = Number(process.env.PORT ?? 3000);
app.listen(port, () => console.log(`listening on ${port}`));
