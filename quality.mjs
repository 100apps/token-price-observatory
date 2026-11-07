export function isReliable(r,now=Date.now()){
 const age=now-Date.parse(r.observed_at);
 return r.provenance==='official'&&!r.stale&&Number.isFinite(age)&&age>=-300000&&age<=48*3600000;
}
