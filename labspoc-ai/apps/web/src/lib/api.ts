const API = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");

export function getFullUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${API}${cleanPath}`;
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const url = getFullUrl(path);
  const r = await fetch(url, {
    ...init,
    headers: {
      ...(init?.headers || {})
    }
  });

  if (!r.ok) {
    const body = await r.json().catch(() => ({ detail: r.statusText }));
    const errorMessage =
      typeof body.detail === "string"
        ? body.detail
        : Array.isArray(body.detail)
        ? body.detail.map((err: any) => err.msg || JSON.stringify(err)).join(", ")
        : body.message || "Request failed";
    throw new Error(errorMessage);
  }

  return r.json();
}

export { API };
