// Editorial shortlist, reviewed 2026-11-07. No usage or popularity counts are inferred.
export const reviewedAt='2026-11-07';
const mainstream=[
 'gpt-6.1-sol','gpt-6.1-terra','gpt-6-astra','gpt-6-luna',
 'claude-sonnet-5.5','claude-opus-5.5','claude-haiku-5.5','claude-fable-5.1',
 'gemini-3.8-flash','gemini-3.7-flash','gemini-3.1-pro-preview','gemini-flash-latest','gemini-pro-latest',
 'qwen3.8-max','qwen3.8-flash','qwen3.7-plus-2026-05-26','qwen-plus','qwen3-coder-flash','qwen3.8-27b',
 'deepseek-flash','deepseek-v4.1-flash','deepseek-v4-pro','deepseek-v3.2',
 'kimi-k3.1-pro','kimi-k3','kimi-k2.7-code','glm-5.3','glm-5.3-flash','glm-5.2',
 'minimax-m3.1-flash','minimax-m3','doubao-seed-2-1-pro-260915','doubao-seed-2-1-lite-260915','doubao-seed-2-1-turbo-260628',
 'grok-4.7','grok-4.6','grok-4.20','grok-code-fast',
 'mistral-large-latest','mistral-medium-latest','mistral-small-latest','codestral-latest','devstral-latest',
 'gpt-oss-120b','llama-4-maverick','llama-4-scout'
];
const preferred={
 bailian:['qwen3.8-max','qwen3.8-flash','qwen3.7-plus-2026-05-26','qwen-plus','qwen3-coder-flash','deepseek-v4-pro','kimi-k3.1-pro','glm-5.3'],
 openrouter:['gpt-6.1-sol','claude-sonnet-5.5','gemini-3.8-flash','deepseek-v4-pro','qwen3.8-max-prime','kimi-k3.1-pro','gpt-6.1-terra','claude-opus-5.5','qwen3.8-flash','glm-5.3']
};
const order=['bailian','deepseek','openai','anthropic','openrouter','siliconflow','gemini','moonshot','zai','minimax','volcengine','tencent','xai','mistral','deepinfra','together_ai','fireworks_ai','bedrock','azure'];
const names={deepinfra:'DeepInfra',fireworks_ai:'Fireworks AI',together_ai:'Together AI',bedrock:'Amazon Bedrock',azure:'Azure OpenAI',xai:'xAI',mistral:'Mistral AI'};
export function platformName(row){return names[row.provider]||row.platform}
export function platformRank(provider){const i=order.indexOf(provider);return i<0?999:i}
const key=s=>s.toLowerCase().replace(/[._]/g,'-');
export function recommendationRank(row){
 const raw=row.model.toLowerCase();
 if(/:|stealth|experimental|legal|robotics/.test(raw))return Infinity;
 const id=key(raw.split('/').at(-1).replace(/^anthropic\./,''));
 const list=[...(preferred[row.provider]||[]),...mainstream];const i=list.map(key).indexOf(id);
 return i<0?Infinity:i;
}
export function groupModels(rows){
 const groups=new Map();
 for(const r of rows){const k=r.model.toLowerCase();if(!groups.has(k))groups.set(k,{key:k,name:r.model,rows:[],rank:recommendationRank(r)});groups.get(k).rows.push(r)}
 return [...groups.values()];
}
export function selectModels(rows,{all=false,search=false,sort='recommended',cost=()=>0,limit=6}={}){
 let groups=groupModels(rows);if(!all&&!search)groups=groups.filter(g=>Number.isFinite(g.rank));
 groups.sort((a,b)=>{
  if(sort==='model')return a.name.localeCompare(b.name);
  if(sort==='cost'||sort==='-cost'){
   const left=Math.min(...a.rows.map(cost)),right=Math.min(...b.rows.map(cost));
   return (sort==='-cost'?right-left:left-right)||a.name.localeCompare(b.name);
  }
  return a.rank-b.rank||a.name.localeCompare(b.name);
 });
 return {total:groups.length,groups:groups.slice(0,limit)};
}
