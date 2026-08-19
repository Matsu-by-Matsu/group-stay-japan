import fs from "node:fs/promises";
import vm from "node:vm";

const PROPERTY_FILE = new URL("../_SYSTEM/property.html", import.meta.url);
const CATALOG_FILE = new URL("../_SYSTEM/catalog.js", import.meta.url);
const EXPECTED_ALLIANCE_ID = "10118837";
const EXPECTED_SID = "328695221";
const EXPECTED_COUNT = 81;
const CHECK_IN = "2026-09-01";
const CHECK_OUT = "2026-09-03";
const ADULTS = "3";

const html = await fs.readFile(PROPERTY_FILE, "utf8");
const catalog = await fs.readFile(CATALOG_FILE, "utf8");
const linkPattern = /'(minn-[^']+)':\{operator:'[^']+',name:'([^']+)'[\s\S]*?partner:'(https:\/\/jp\.trip\.com\/[^']+)'/g;
const links = [...html.matchAll(linkPattern)].map((match) => ({ id: match[1], name: match[2], url: match[3] }));
const catalogContext = { window: {} };
vm.createContext(catalogContext);
vm.runInContext(catalog, catalogContext);
for (const [id, property] of Object.entries(catalogContext.window.GSJ_EXTRA_PROPERTIES || {})) links.push({ id, name: property.name, url: property.partner });

const failures = [];
const results = [];
if (links.length !== EXPECTED_COUNT) failures.push(`Expected ${EXPECTED_COUNT} affiliate links, found ${links.length}.`);
if (new Set(links.map((link) => link.id)).size !== links.length) failures.push("Property ids are not unique.");

for (const link of links) {
  const source = new URL(link.url);
  const hotelId = source.pathname.match(/hotel-detail-(\d+)/)?.[1];
  if (source.hostname !== "jp.trip.com") failures.push(`${link.id}: unexpected host ${source.hostname}`);
  if (!hotelId) failures.push(`${link.id}: destination is not an individual Trip.com hotel page`);
  if (source.searchParams.get("Allianceid") !== EXPECTED_ALLIANCE_ID) failures.push(`${link.id}: Allianceid is missing or incorrect`);
  if (source.searchParams.get("SID") !== EXPECTED_SID) failures.push(`${link.id}: SID is missing or incorrect`);
  if (source.searchParams.get("trip_sub1") !== link.id) failures.push(`${link.id}: trip_sub1 does not match property id`);
  if (!source.searchParams.get("trip_sub3")) failures.push(`${link.id}: trip_sub3 is missing`);
}

const normalize = (value) => value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
const ignored = new Set(["hotel", "tokyo", "kyoto", "osaka", "grand", "base"]);
const nameTokens = (value) => normalize(value).split(" ").filter((token) => token.length > 2 && !ignored.has(token));

async function checkLive(link) {
  const source = new URL(link.url);
  const hotelId = source.pathname.match(/hotel-detail-(\d+)/)?.[1];
  const adId = source.searchParams.get("trip_sub3");
  source.searchParams.set("checkIn", CHECK_IN);
  source.searchParams.set("checkOut", CHECK_OUT);
  source.searchParams.set("adult", ADULTS);
  try {
    const response = await fetch(source, { redirect: "follow", signal: AbortSignal.timeout(30_000), headers: { "user-agent": "Mozilla/5.0 (compatible; GroupStayJapan-LinkMonitor/2.0)", "accept-language": "en-US,en;q=0.9,ja;q=0.8" } });
    const finalUrl = new URL(response.url);
    const body = await response.text();
    const normalizedBody = normalize(body.slice(0, 1_500_000));
    const tokens = nameTokens(link.name);
    const nameMatched = tokens.length === 0 || tokens.every((token) => normalizedBody.includes(token));
    const ok = response.ok && finalUrl.hostname === "jp.trip.com" && Boolean(hotelId) && finalUrl.pathname.includes(`hotel-detail-${hotelId}`) && finalUrl.searchParams.get("Allianceid") === EXPECTED_ALLIANCE_ID && finalUrl.searchParams.get("SID") === EXPECTED_SID && finalUrl.searchParams.get("trip_sub1") === link.id && finalUrl.searchParams.get("trip_sub3") === adId && nameMatched;
    results.push({ id: link.id, status: response.status, finalUrl: finalUrl.href, ok, nameMatched });
    if (!ok) failures.push(`${link.id}: live destination, property identity, or tracking check failed (${response.status}, ${finalUrl.href})`);
  } catch (error) {
    results.push({ id: link.id, status: "ERROR", finalUrl: "", ok: false, nameMatched: false });
    failures.push(`${link.id}: request failed: ${error.message}`);
  }
}

const concurrency = 6;
for (let index = 0; index < links.length; index += concurrency) await Promise.all(links.slice(index, index + concurrency).map(checkLive));
console.table(results.map(({ id, status, ok, nameMatched, finalUrl }) => ({ id, status, ok, nameMatched, destination: finalUrl ? new URL(finalUrl).pathname : "-" })));
console.log(`Checked ${links.length} Trip.com affiliate links at ${new Date().toISOString()}.`);
if (failures.length) { console.error("\nAffiliate link monitor failed:\n- " + failures.join("\n- ")); process.exit(1); }
console.log("All affiliate links resolve to the intended individual hotel page and retain the expected tracking parameters.");
