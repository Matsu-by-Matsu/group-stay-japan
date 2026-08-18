import fs from "node:fs/promises";

const PROPERTY_FILE = new URL("../_SYSTEM/property.html", import.meta.url);
const EXPECTED_ALLIANCE_ID = "10118837";
const EXPECTED_SID = "328695221";
const EXPECTED_COUNT = 21;
const CHECK_IN = "2026-09-01";
const CHECK_OUT = "2026-09-03";
const ADULTS = "3";

const html = await fs.readFile(PROPERTY_FILE, "utf8");
const linkPattern = /'(minn-[^']+)':\{[\s\S]*?partner:'(https:\/\/jp\.trip\.com\/[^']+)'/g;
const links = [...html.matchAll(linkPattern)].map((match) => ({
  id: match[1],
  url: match[2],
}));

const failures = [];
const results = [];

if (links.length !== EXPECTED_COUNT) {
  failures.push(`Expected ${EXPECTED_COUNT} affiliate links, found ${links.length}.`);
}

const paths = new Set();
const adIds = new Set();

for (const link of links) {
  const source = new URL(link.url);
  const hotelId = source.pathname.match(/hotel-detail-(\d+)/)?.[1];
  const adId = source.searchParams.get("trip_sub3");

  if (source.hostname !== "jp.trip.com") failures.push(`${link.id}: unexpected host ${source.hostname}`);
  if (source.searchParams.get("Allianceid") !== EXPECTED_ALLIANCE_ID) failures.push(`${link.id}: Allianceid is missing or incorrect`);
  if (source.searchParams.get("SID") !== EXPECTED_SID) failures.push(`${link.id}: SID is missing or incorrect`);
  if (source.searchParams.get("trip_sub1") !== link.id) failures.push(`${link.id}: trip_sub1 does not match property id`);
  if (!adId) failures.push(`${link.id}: trip_sub3 is missing`);
  if (!hotelId) failures.push(`${link.id}: Trip.com hotel id is missing from path`);

  paths.add(source.pathname);
  if (adId) adIds.add(adId);

  source.searchParams.set("checkIn", CHECK_IN);
  source.searchParams.set("checkOut", CHECK_OUT);
  source.searchParams.set("adult", ADULTS);

  try {
    const response = await fetch(source, {
      redirect: "follow",
      signal: AbortSignal.timeout(30_000),
      headers: {
        "user-agent": "Mozilla/5.0 (compatible; GroupStayJapan-LinkMonitor/1.0)",
        "accept-language": "ja-JP,ja;q=0.9,en;q=0.8",
      },
    });
    const finalUrl = new URL(response.url);
    const ok =
      response.ok &&
      finalUrl.hostname === "jp.trip.com" &&
      finalUrl.pathname.includes(`hotel-detail-${hotelId}`) &&
      finalUrl.searchParams.get("Allianceid") === EXPECTED_ALLIANCE_ID &&
      finalUrl.searchParams.get("SID") === EXPECTED_SID &&
      finalUrl.searchParams.get("trip_sub1") === link.id &&
      finalUrl.searchParams.get("trip_sub3") === adId;

    results.push({ id: link.id, status: response.status, finalUrl: finalUrl.href, ok });
    if (!ok) failures.push(`${link.id}: live redirect or tracking check failed (${response.status}, ${finalUrl.href})`);
  } catch (error) {
    results.push({ id: link.id, status: "ERROR", finalUrl: "", ok: false });
    failures.push(`${link.id}: request failed: ${error.message}`);
  }
}

if (paths.size !== links.length) failures.push(`Destination paths are not unique: ${paths.size}/${links.length}`);
if (adIds.size !== links.length) failures.push(`trip_sub3 values are not unique: ${adIds.size}/${links.length}`);

console.table(results.map(({ id, status, ok, finalUrl }) => ({ id, status, ok, destination: finalUrl ? new URL(finalUrl).pathname : "-" })));
console.log(`Checked ${links.length} Trip.com affiliate links at ${new Date().toISOString()}.`);

if (failures.length) {
  console.error("\nAffiliate link monitor failed:\n- " + failures.join("\n- "));
  process.exit(1);
}

console.log("All affiliate links are healthy and retain the expected tracking parameters.");
