// Pick a clearly labelled regular quote, never the cheapest hidden condition.
export function regularRank(r){
 const s=String(r.variant||'').toLowerCase();let rank=0;
 if(/batch/.test(s))rank+=100;
 if(/priority|ultrafast|fast/.test(s)&&!s.includes('实时'))rank+=30;
 if(/思考/.test(s)&&!/非思考/.test(s))rank+=10;
 if(/闲时|off.peak/.test(s))rank+=3;
 if(/美国|新加坡|国际/.test(s))rank+=8;
 const range=r.conditions?.context_range||s;
 const match=String(range).match(/(?:^|\|\s*)(\d+)\s*[kKmM]\s*[<＜]/);
 if(match)rank+=5;
 return rank;
}
export function chooseQuote(rows,id){return rows.find(r=>r.id===id)||rows.slice().sort((a,b)=>regularRank(a)-regularRank(b)||a.id.localeCompare(b.id))[0]}
export function costParts(r,input,output,hit){
 const cached=r.cache_supported===false?0:input*hit;
 return{uncached:(input-cached)*r.input/1e6,cached:cached*(r.cache_read??r.input)/1e6,output:output*r.output/1e6};
}

// Sort a copy: URL selection order remains stable when usage or FX changes.
export function rankQuotes(rows,cost){return rows.slice().sort((a,b)=>{
 const av=cost(a),bv=cost(b),x=Number.isFinite(av)?av:Infinity,y=Number.isFinite(bv)?bv:Infinity;
 return x===y?a.id.localeCompare(b.id):x-y;
})}
