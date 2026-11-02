// Temporary list; replace with a KvK lookup or database query later
export const COMPANIES = [
  "FrieslandCampina",
  "Vion Food Group",
  "Cosun",
  "Avebe",
  "Agrifirm",
  "ForFarmers",
  "Nutreco",
  "Rijk Zwaan",
  "Enza Zaden",
  "Bejo Zaden",
];

const normalize = (s) =>
  s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();

// Companies matching the typed text, best match first
export function findCompanies(text, limit = 5) {
  const q = normalize(text.trim());
  if (!q) return [];
  return COMPANIES.map((name) => {
    const n = normalize(name);
    const rank = n.startsWith(q) ? 0 : n.split(/\s+/).some((w) => w.startsWith(q)) ? 1 : n.includes(q) ? 2 : -1;
    return { name, rank };
  })
    .filter((c) => c.rank >= 0)
    .sort((a, b) => a.rank - b.rank || a.name.localeCompare(b.name))
    .slice(0, limit)
    .map((c) => c.name);
}
