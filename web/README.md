# InspectPin web dashboard

The React/TypeScript dashboard uses only the versioned backend API. It never
generates battery, connectivity or inspection values in the browser; simulator
records are visibly labelled.

```powershell
cd web
npm install
npm run dev
```

Vite proxies `/api` to `http://127.0.0.1:5000` in development. For a production
build run `npm run build` and serve `dist` behind the same HTTPS origin as the
backend or configure a tightly restricted production CORS origin.
