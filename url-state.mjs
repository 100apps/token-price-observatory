export const defaults={input:100000000,output:100000000,cache:90,fx:null,fxMode:'auto',currency:'CNY',search:'',provider:'',trust:'reliable',sort:'recommended',openPlatforms:'bailian,deepseek,openai,anthropic',openModels:'',closedModels:'',fullCatalog:'',tab:'prices',compareSearch:'',historyModel:'',historyRange:'30'};
const choices={fxMode:['auto','manual'],currency:['USD','CNY'],trust:['reliable','official','community',''],sort:['recommended','cost','-cost','model','provider'],tab:['prices','compare','history','sources'],historyRange:['30','90','0']};
export function normalize(state={}){
 const result={...defaults};
 for(const key of Object.keys(result)){
  const v=state[key];if(v==null)continue;
  if(['input','output','cache','fx'].includes(key)){
   const n=typeof v==='string'&&v.trim()===''?NaN:Number(v);
   const valid=Number.isFinite(n)&&(key==='fx'?n>=.01&&n<=1e6:key==='cache'?n>=0&&n<=100:n>=0&&n<=Number.MAX_SAFE_INTEGER&&Number.isInteger(n));
   if(valid)result[key]=n;
  }else if(choices[key]){if(choices[key].includes(v))result[key]=v}
  else result[key]=String(v).slice(0,1000);
 }
 return result;
}
export function readState(url){const raw=Object.fromEntries(new URL(url).searchParams);if(normalize({fx:raw.fx}).fx!==null&&!raw.fxMode)raw.fxMode='manual';return normalize(raw)}
export function writeState(url,state){const u=new URL(url),s=normalize(state);for(const k of Object.keys(defaults))s[k]==null?u.searchParams.delete(k):u.searchParams.set(k,String(s[k]));return u.href}
