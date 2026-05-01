const KEY = "gamerec_archetype";

export type ArchetypeIdentity = {
  archetype: string;
  confidence: number;
};

export function readArchetypeIdentity(): ArchetypeIdentity | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as ArchetypeIdentity;
    if (!parsed?.archetype) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function writeArchetypeIdentity(value: ArchetypeIdentity): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(value));
  } catch {
    // best effort only
  }
}
