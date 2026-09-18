export function japaneseRoomSize(value) {
 const s=String(value??'').trim();
 if(!s||s==='Room-dependent')return '客室タイプによる';
 const unit=s.replace(/(?:㎡|m²|sqm)/gi,'㎡');
 let m=unit.match(/^([\d.]+)㎡ room available$/i);if(m)return `${m[1]}㎡の客室あり`;
 m=unit.match(/^Up to ([\d.]+)㎡$/i);if(m)return `最大${m[1]}㎡`;
 if(/^[\d.]+(?:[–−-][\d.]+)?㎡\+?$/.test(unit))return unit.replace(/㎡\+$/,'㎡以上');
 return '客室タイプによる';
}
