export function calculate(r,input,output,hit){return (input*((1-hit)*r.input+hit*(r.cache_read??r.input))+output*r.output)/1e6}
export function convert(value,from,to,fx){return value*(from===to?1:from==='USD'?fx:1/fx)}
