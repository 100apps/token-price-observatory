import{test}from'node:test';import assert from'node:assert/strict';import{selectModels,recommendationRank,groupModels}from'../catalog.mjs';
const row=(model,variant='standard')=>({provider:'openrouter',model,variant});
test('recommended models replace free, obscure and dated entries in default view',()=>{
 const rows=[row('stealth/crouton-alpha'),row('random/unknown'),row('openai/gpt-6.1-sol:free'),row('openai/gpt-6.1-sol-2026-10-01'),row('openai/gpt-6.1-sol'),row('anthropic/claude-sonnet-5.5')];
 const result=selectModels(rows);assert.deepEqual(result.groups.map(g=>g.name),['openai/gpt-6.1-sol','anthropic/claude-sonnet-5.5']);
 assert.equal(selectModels(rows,{all:true,limit:100}).groups.length,6);assert.equal(selectModels([row('random/unknown')],{search:true}).groups.length,1);
});
test('variants occupy one model entry and preserve every quote',()=>{
 const rs=[row('openai/gpt-6.1-sol'),row('openai/gpt-6.1-sol','batch'),row('openai/gpt-6.1-sol','priority')];
 assert.equal(groupModels(rs).length,1);assert.equal(selectModels(rs).groups[0].rows.length,3);
});
test('each platform is independently limited to six models; no random fallback',()=>{
 const rows=['gpt-6.1-sol','claude-sonnet-5.5','gemini-3.8-flash','deepseek-v4-pro','qwen3.8-max-prime','kimi-k3.1-pro','gpt-6.1-terra'].map(x=>row('vendor/'+x));
 assert.equal(selectModels(rows).groups.length,6);assert.equal(selectModels(rows).total,7);assert.equal(selectModels([row('random/unknown')]).groups.length,0);
});
test('explicit sorting is applied inside the selected platform',()=>{
 const rs=[row('openai/gpt-6.1-sol'),row('anthropic/claude-sonnet-5.5')];
 assert.equal(selectModels(rs,{sort:'cost',cost:r=>r.model.startsWith('anthropic')?1:5}).groups[0].name,'anthropic/claude-sonnet-5.5');
});
