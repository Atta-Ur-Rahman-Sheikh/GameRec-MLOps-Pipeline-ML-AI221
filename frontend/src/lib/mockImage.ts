const COLORS = [
  ["#20173a", "#6441a5"],
  ["#12222f", "#2a596e"],
  ["#22161a", "#6b233a"],
  ["#1e2228", "#3d4f66"],
  ["#1a2416", "#3f7d34"],
];

export function imageFallbackForTitle(title: string): string {
  const seed = [...title].reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const [c1, c2] = COLORS[seed % COLORS.length];
  const safeTitle = title.slice(0, 32).replace(/[<>&"]/g, "");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="680"><defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="${c1}" /><stop offset="100%" stop-color="${c2}" /></linearGradient></defs><rect width="100%" height="100%" fill="url(#bg)" /><circle cx="1000" cy="120" r="180" fill="rgba(255,255,255,0.07)" /><circle cx="140" cy="620" r="260" fill="rgba(255,255,255,0.05)" /><text x="72" y="370" fill="white" font-size="54" font-family="Segoe UI, Inter, Arial, sans-serif" font-weight="700">${safeTitle}</text></svg>`;
  return `data:image/svg+xml;base64,${toBase64(svg)}`;
}

function toBase64(value: string): string {
  try {
    return btoa(unescape(encodeURIComponent(value)));
  } catch {
    return "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMjAwIiBoZWlnaHQ9IjY4MCI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iIzFlMWUxZSIgLz48L3N2Zz4=";
  }
}
