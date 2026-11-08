export function calculate(r,input,output,hit){if(r.calculation_blocked)return NaN;return (input*((1-hit)*r.input+hit*(r.cache_read??r.input))+output*r.output)/1e6}
export function convert(value,from,to,fx){if(from===to)return value;if(!Number.isFinite(fx)||fx<=0)return NaN;return value*(from==='USD'?fx:1/fx)}
export function formatTokenCount(raw){
 const empty=String(raw).trim()==='',n=empty?100000000:Number(raw);
 if(!Number.isSafeInteger(n)||n<0)return '—';
 const [unit,label]=n>=1e12?[1e12,'万亿']:n>=1e8?[1e8,'亿']:n>=1e4?[1e4,'万']:[1,''];
 const scaled=n/unit,rounded=Number(scaled.toFixed(4));
 return (empty?'默认 ':'')+(Math.abs(rounded*unit-n)>.001?'约 ':'')+new Intl.NumberFormat('zh-CN',{maximumFractionDigits:4}).format(rounded)+(label?' '+label:'');
}
