import { createReadStream } from "node:fs";
import { stat } from "node:fs/promises";
import { createServer } from "node:http";
import { extname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = fileURLToPath(new URL(".", import.meta.url));
const distDir = join(rootDir, "dist");
const indexFile = join(distDir, "index.html");
const port = Number(process.env.PORT ?? "3000");

const contentTypes = new Map([
  [".css", "text/css; charset=utf-8"],
  [".html", "text/html; charset=utf-8"],
  [".ico", "image/x-icon"],
  [".js", "text/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".map", "application/json; charset=utf-8"],
  [".png", "image/png"],
  [".svg", "image/svg+xml; charset=utf-8"],
  [".txt", "text/plain; charset=utf-8"],
  [".woff", "font/woff"],
  [".woff2", "font/woff2"]
]);

async function isFile(filePath) {
  try {
    return (await stat(filePath)).isFile();
  } catch {
    return false;
  }
}

function writeJson(res, statusCode, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body)
  });
  res.end(body);
}

async function sendFile(req, res, filePath) {
  const fileStat = await stat(filePath);
  res.writeHead(200, {
    "Content-Type": contentTypes.get(extname(filePath)) ?? "application/octet-stream",
    "Content-Length": fileStat.size
  });

  if (req.method === "HEAD") {
    res.end();
    return;
  }

  createReadStream(filePath).pipe(res);
}

function resolveRequestPath(pathname) {
  try {
    const segments = pathname
      .split("/")
      .filter(Boolean)
      .map((segment) => decodeURIComponent(segment));

    return resolve(distDir, ...segments);
  } catch {
    return null;
  }
}

const server = createServer(async (req, res) => {
  const method = req.method ?? "GET";

  if (method !== "GET" && method !== "HEAD") {
    writeJson(res, 405, { message: "Method Not Allowed" });
    return;
  }

  const url = new URL(req.url ?? "/", `http://${req.headers.host ?? "localhost"}`);
  const { pathname } = url;

  if (pathname === "/health") {
    writeJson(res, 200, { status: "ok", service: "frontend" });
    return;
  }

  let targetFile = pathname === "/" ? indexFile : resolveRequestPath(pathname);

  if (!targetFile) {
    writeJson(res, 400, { message: "Bad Request" });
    return;
  }

  const relativePath = relative(distDir, targetFile);
  const isInsideDist =
    relativePath === "" || (!relativePath.startsWith("..") && !relativePath.includes(":"));

  if (!isInsideDist) {
    writeJson(res, 403, { message: "Forbidden" });
    return;
  }

  if (!(await isFile(targetFile))) {
    if (extname(pathname)) {
      writeJson(res, 404, { message: "Not Found" });
      return;
    }

    targetFile = indexFile;
  }

  if (!(await isFile(targetFile))) {
    writeJson(res, 500, { message: "Build output not found. Run npm run build first." });
    return;
  }

  try {
    await sendFile(req, res, targetFile);
  } catch {
    writeJson(res, 500, { message: "Failed to serve static asset." });
  }
});

server.listen(port, "0.0.0.0", () => {
  console.log(`Frontend server listening on port ${port}`);
});
