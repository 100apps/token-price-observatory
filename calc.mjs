export function calculate(r,input,output,hit){return (input*((1-hit)*r.input+hit*(r.cache_read??r.input))+output*r.output)/1e6}
export function convert(value,from,to,fx){if(from===to)return value;if(!Number.isFinite(fx)||fx<=0)return NaN;return value*(from==='USD'?fx:1/fx)}
