import fs from "node:fs/promises";
import vm from "node:vm";

const file = new URL("../_SYSTEM/catalog.js", import.meta.url);
const code = await fs.readFile(file, "utf8");
const context = { window: {} };
vm.createContext(context);
vm.runInContext(code, context);

const exact = {
  "mimaru-suites-tokyo-asakusa":["tokyo",100383864,"mimaru-suites-tokyo-asakusa"],
  "mimaru-tokyo-station-east":["tokyo",92435119,"mimaru-tokyo-station-east"],
  "mimaru-ueno-east":["tokyo",21864150,"mimaru-tokyo-ueno-east"],
  "mimaru-kinshicho":["tokyo",92027017,"mimaru-tokyo-kinshicho"],
  "mimaru-suites-tokyo-nihombashi":["tokyo",99803618,"mimaru-suites-tokyo-nihombashi"],
  "mimaru-akasaka":["tokyo",14201935,"mimaru-tokyo-akasaka"],
  "mimaru-ueno-inaricho":["tokyo",21862382,"mimaru-tokyo-ueno-inaricho"],
  "mimaru-ueno-north":["tokyo",13671810,"mimaru-tokyo-ueno-north"],
  "mimaru-ueno-okachimachi":["tokyo",48708872,"mimaru-tokyo-ueno-okachimachi"],
  "mimaru-suitengumae":["tokyo",15835393,"mimaru-tokyo-nihombashi-suitengumae"],
  "mimaru-hatchobori":["tokyo",25195209,"mimaru-tokyo-hatchobori"],
  "mimaru-asakusa-station":["tokyo",72683080,"mimaru-tokyo-asakusa-station"],
  "mimaru-shinjuku-west":["tokyo",54552657,"mimaru-tokyo-shinjuku-west"],
  "mimaru-ginza-east":["tokyo",47990998,"mimaru-tokyo-ginza-east"],
  "mimaru-ikebukuro":["tokyo",99965689,"mimaru-tokyo-ikebukuro"],
  "mimaru-nijo-castle":["kyoto",15837901,"mimaru-kyoto-horikawarokkaku"],
  "mimaru-shinmachi-sanjo":["kyoto",21869140,"mimaru-kyoto-shinmachi-sanjo"],
  "mimaru-suites-kyoto-central":["kyoto",80625249,"mimaru-suites-kyoto-central"],
  "mimaru-kawaramachi-gojo":["kyoto",48033361,"mimaru-kyoto-kawaramachi-gojo"],
  "mimaru-kyoto-station":["minami-ward",40694354,"mimaru-kyoto-station"],
  "mimaru-shijo-west":["kyoto",23216862,"mimaru-kyoto-shijo-west"],
  "mimaru-suites-kyoto-shijo":["kyoto",78123223,"mimaru-suites-kyoto-shijo"],
  "mimaru-namba-north":["osaka",69272905,"mimaru-osaka-namba-north"],
  "mimaru-namba-station":["osaka",94176886,"mimaru-osaka-namba-station"],
  "mimaru-shinsaibashi-east":["osaka",100367501,"mimaru-osaka-shinsaibashi-east"],
  "mimaru-shinsaibashi-north":["osaka",101975475,"mimaru-osaka-shinsaibashi-north"],
  "mimaru-shinsaibashi-west":["osaka",56996772,"mimaru-osaka-shinsaibashi-west"],
  "fav-tokyoryogoku":["tokyo",104573901,"fav-tokyo-ryogoku"],
  "fav-tokyonishinippori":["tokyo",100697710,"fav-tokyo-nishinippori"],
  "fav-hiroshimaheiwaodori":["hiroshima",100902929,"fav-hiroshima-heiwaodori"],
  "fav-hiroshima-stadium":["hiroshima",95265781,"fav-hiroshima-stadium"],
  "fav-kagoshimachuo":["kagoshima",99996811,"fav-kagoshima-chuo"],
  "fav-hakodate":["hakodate",96211866,"fav-hakodate"],
  "fav-ise":["ise",81141277,"fav-ise"],
  "fav-kumamoto":["kumamoto",80965528,"fav-kumamoto"],
  "fav-takamatsu":["takamatsu",66670814,"fav-hotel-takamatsu"],
  "fav-takayama":["takayama",68165277,"fav-hidatakayama"],
  "fav-lux-sapporosusukino":["sapporo",128565521,"fav-lux-sapporo-susukino"],
  "fav-lux-miyazaki":["miyazaki",132922484,"fav-lux-miyazaki"],
  "fav-lux-nagasaki":["nagasaki",114677761,"fav-lux-nagasaki"],
  "fav-lux-hidatakayama":["takayama",109253572,"fav-lux-hida-takayama"],
  "fav-lux-kagoshimatenmonkan":["kagoshima",124582676,"fav-lux-kagoshima-tenmonkan"],
  "grand-base-gb-saiwaimachi":["nagasaki",80942978,"grand-base-saiwaimachi"],
  "grand-base-gb-nagasakicity":["nagasaki",66771461,"grand-base-nagasaki-city"],
  "grand-base-gb-urakami":["nagasaki",71981292,"grand-base-urakami"],
  "grand-base-nagasaki-nakamachi":["nagasaki",81075011,"grand-base-nagasaki-nakamachi"],
  "grand-base-gb-osu":["nagoya",54710698,"grand-base-osu"],
  "grand-base-gb-hakatabay":["fukuoka",66770966,"grand-base-hakata-bay"],
  "grand-base-gb-crane":["fukuoka",56996738,"grand-base-crane"],
  "grand-base-gb-yakuinodori":["fukuoka",61797409,"grand-base-yakuin-odori"],
  "grand-base-gb-mojiko":["kita-kyushu",42190334,"grand-base-mojiko"],
  "grand-base-gb-mojinagomi":["kita-kyushu",58404878,"grand-base-moji-nagomi"],
  "grand-base-gb-karatsuekiminami":["karatsu",35952942,"grand-base-karatsuekiminami"],
  "grand-base-gb-beppuekimae":["beppu",38405334,"grand-base-beppuekimae"],
  "grand-base-gb-beppueki":["beppu",51195935,"grand-base-beppueki"],
  "grand-base-gb-beppuekihigashi":["beppu",54147050,"grand-base-beppu-ekihigashi"],
  "grand-base-gb-hiroshimaekimae":["hiroshima",50215893,"grand-base-hiroshimaekimae"],
  "grand-base-gb-okayamaekimae":["okayama",66773024,"grand-base-okayama-ekimae"],
  "grand-base-gb-kurashikichuo":["kurashiki",58860588,"grand-base-kurashiki-chuo"],
  "grand-base-gb-kagoshima-tenmonkan":["kagoshima",69150490,"grand-base-kagoshima-tenmonkan"]
};

const stays = (context.window.GSJ_EXTRA_STAYS || []).filter((stay) => exact[stay.id]);
const properties = {};
for (const stay of stays) {
  const property = context.window.GSJ_EXTRA_PROPERTIES[stay.id];
  const [city, hotelId, slug] = exact[stay.id];
  const url = new URL(`https://jp.trip.com/hotels/${city}-hotel-detail-${hotelId}/${slug}/`);
  url.searchParams.set("Allianceid", "10118837");
  url.searchParams.set("SID", "328695221");
  url.searchParams.set("trip_sub1", stay.id);
  url.searchParams.set("trip_sub3", "D19292009");
  property.partner = url.href;
  property.tripHotelId = String(hotelId);
  property.partnerVerified = true;
  properties[stay.id] = property;
}

await fs.writeFile(file, `window.GSJ_EXTRA_STAYS=${JSON.stringify(stays)};\nwindow.GSJ_EXTRA_PROPERTIES=${JSON.stringify(properties)};\n`, "utf8");
console.log(`Updated ${stays.length} exact Trip.com links; removed ${Object.keys(context.window.GSJ_EXTRA_PROPERTIES).length - stays.length} unresolved properties.`);
