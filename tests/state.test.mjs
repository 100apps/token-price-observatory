import{test}from'node:test';import assert from'node:assert/strict';import{defaults,readState,writeState}from'../url-state.mjs';import{isReliable}from'../quality.mjs';
test('share URL round trip including zero usage, 0% cache, currency and Chinese search',()=>{
 const state={...defaults,input:0,output:1234567,cache:0,fx:7.01,currency:'CNY',search:'千问 & 思考',provider:'bailian',sort:'-cost',tab:'compare',compareSearch:'qwen-plus',historyModel:'a:b | x',quotes:JSON.stringify({'bailian|qwen-plus':'北京 | Batch Chat'}),pinned:JSON.stringify(['quote-a','quote-b'])};
 const url=writeState('https://example.com/repo/?tracking=keep',state);assert.deepEqual(readState(url),state);assert.equal(new URL(url).searchParams.get('tracking'),'keep');
});
test('empty, nonfinite, negative and malformed URL parameters use valid defaults',()=>{
 const state=readState('https://example.com/?input=-1&output=Infinity&cache=101&fx=0&currency=BAD&tab=bad&trust=x');
 assert.deepEqual(state,defaults);assert.equal(readState('https://example.com/?input=&cache=NaN').input,1e8);
});
test('fresh official only; old, failed, community and future timestamps excluded',()=>{
 const now=Date.parse('2026-11-07T12:00:00Z'),r={provenance:'official',observed_at:'2026-11-07T11:00:00Z',stale:false};
 assert.equal(isReliable(r,now),true);for(const override of [{stale:true},{provenance:'community'},{observed_at:'bad'},{observed_at:'2026-11-01T00:00:00Z'},{observed_at:'2026-11-08T00:00:00Z'}])assert.equal(isReliable({...r,...override},now),false);
});
test('new visits default to CNY and automatic FX; old explicit rates stay manual',()=>{
 assert.equal(readState('https://example.com/').currency,'CNY');assert.equal(readState('https://example.com/').fxMode,'auto');assert.equal(readState('https://example.com/?fx=7.1').fxMode,'manual');assert.equal(readState('https://example.com/?fx=7.1&fxMode=auto').fxMode,'auto');
});
test('blocked official prices never qualify as reliable',()=>{
 assert.equal(isReliable({provenance:'official',stale:false,observed_at:new Date().toISOString(),calculation_blocked:true}),false);
});
