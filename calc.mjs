export function costParts(r,input,output,hit){
 const cached=r.cache_supported===false?0:input*hit;
 return{uncached:(input-cached)*r.input/1e6,cached:cached*(r.cache_read??r.input)/1e6,output:output*r.output/1e6};
}
export function calculate(r,input,output,hit){if(r.calculation_blocked)return NaN;const p=costParts(r,input,output,hit);return p.uncached+p.cached+p.output}
export function convert(value,from,to,fx){
 if(!['USD','CNY'].includes(from)||!['USD','CNY'].includes(to))return NaN;
 if(from===to)return value;
 if(!Number.isFinite(fx)||fx<=0)return NaN;
 return from==='USD'?value*fx:value/fx;
}
// Unit prices preserve small source rates; only suppress binary floating-point tails.
// Formatting is never used as an input to the calculator.
export function formatUnitRate(n,currency){
 if(n==null)return '未知';
 if(!Number.isFinite(n)||!['USD','CNY'].includes(currency))return '单价不可用';
 const clean=Number(n.toPrecision(15));
 return new Intl.NumberFormat('zh-CN',{style:'currency',currency,minimumFractionDigits:2,maximumFractionDigits:20}).format(clean);
}
export function formatTokenCount(raw){
 const empty=String(raw).trim()==='',n=empty?100000000:Number(raw);
 if(!Number.isSafeInteger(n)||n<0)return '—';
 const [unit,label]=n>=1e12?[1e12,'万亿']:n>=1e8?[1e8,'亿']:n>=1e4?[1e4,'万']:[1,''];
 const scaled=n/unit,rounded=Number(scaled.toFixed(4));
 return (empty?'默认 ':'')+(Math.abs(rounded*unit-n)>.001?'约 ':'')+new Intl.NumberFormat('zh-CN',{maximumFractionDigits:4}).format(rounded)+(label?' '+label:'');
}
