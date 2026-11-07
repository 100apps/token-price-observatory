export const defaults={input:100000000,output:100000000,cache:90,fx:7.2,currency:'USD',search:'',provider:'',trust:'reliable',sort:'cost',tab:'prices',compareSearch:'',historyModel:'',historyRange:'30'};
const choices={currency:['USD','CNY'],trust:['reliable','official','community',''],sort:['cost','-cost','model','provider'],tab:['prices','compare','history','sources'],historyRange:['30','90','0']};
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
export function readState(url){return normalize(Object.fromEntries(new URL(url).searchParams))}
export function writeState(url,state){const u=new URL(url),s=normalize(state);for(const k of Object.keys(defaults))u.searchParams.set(k,String(s[k]));return u.href}
