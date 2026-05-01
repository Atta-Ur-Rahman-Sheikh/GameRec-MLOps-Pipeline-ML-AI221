/** Best-effort message from thrown API client errors or FastAPI JSON bodies. */

function extractDetail(raw: string): string | undefined {
  try {
    const o = JSON.parse(raw) as { detail?: unknown };
    if (typeof o.detail === "string") return o.detail;
    if (Array.isArray(o.detail)) {
      return o.detail
        .map((e) =>
          typeof e === "object" && e !== null && "msg" in e ? String((e as { msg: string }).msg) : JSON.stringify(e)
        )
        .join("; ");
    }
    return typeof o.detail === "object" && o.detail !== null ? JSON.stringify(o.detail) : undefined;
  } catch {
    return undefined;
  }
}

export function messageFromFetchError(error: unknown): string {
  if (!(error instanceof Error)) {
    return String(error);
  }

  let raw = error.message.trim();

  if (raw.startsWith("<")) {
    return "Server returned a non‑JSON response. Restart the backend so `/discover/cluster-map` exists and matches this frontend.";
  }

  const parsed = extractDetail(raw);
  if (parsed !== undefined) {
    raw = parsed;
  } else if (/\{[\s\S]*\}/g.test(raw)) {
    const m = raw.match(/\{[\s\S]*$/);
    if (m) {
      const nested = extractDetail(m[0]);
      if (nested !== undefined) raw = nested;
    }
  }

  if (/^Request failed with status 404\b/i.test(raw) || /\b404\b/.test(raw)) {
    return "Route not found (404). Restart FastAPI with the latest code so `GET /discover/cluster-map` is registered.";
  }

  return raw;
}
