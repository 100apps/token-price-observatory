import{test}from'node:test';import assert from'node:assert/strict';import{calculate,convert,formatUnitRate}from'../calc.mjs';
test('90% cache, 100m input/output: independently derived invoice',()=>{assert.equal(calculate({input:2,output:8,cache_read:.2},1e8,1e8,.9),838)});
test('unknown cache uses normal input; free cache remains zero',()=>{assert.equal(calculate({input:2,output:8,cache_read:null},1e6,1e6,.9),10);assert.equal(calculate({input:2,output:8,cache_read:0},1e6,0,1),0)});
test('zero usage and currency round trip',()=>{assert.equal(calculate({input:2,output:8},0,0,0),0);assert.ok(Math.abs(convert(convert(123,'USD','CNY',7.2),'CNY','USD',7.2)-123)<1e-9)});
test('missing exchange rate cannot turn USD costs into free CNY prices',()=>{
 assert.ok(Number.isNaN(convert(100,'USD','CNY',null)));assert.ok(Number.isNaN(convert(100,'CNY','USD',0)));assert.equal(convert(100,'CNY','CNY',null),100);
});
test('unverified Bailian list prices are never computed as promotion prices',()=>{
 assert.ok(Number.isNaN(calculate({input:1,output:2,cache_read:.1,calculation_blocked:true},1e8,1e8,.9)));
});
test('same-currency amounts bypass exchange rates exactly; unsupported currencies fail closed',()=>{
 for(const c of ['USD','CNY'])for(const fx of [null,NaN,0,6.671294223018361])assert.equal(convert(.044,c,c,fx),.044);
 assert.ok(Number.isNaN(convert(1,'EUR','CNY',7)));assert.ok(Number.isNaN(convert(1,'EUR','EUR',7)));
});
test('explicitly unsupported caching is ignored in both total and cost decomposition',()=>{
 const r={input:2,output:4,cache_read:.1,cache_supported:false};assert.equal(calculate(r,1e8,1e8,.9),600);
});

test('native unit prices preserve fractional cents and suppress binary conversion noise',()=>{
 assert.match(formatUnitRate(.044,'USD'),/0\.044$/);assert.match(formatUnitRate(.006,'USD'),/0\.006$/);
 assert.match(formatUnitRate(.39999999999999997,'USD'),/0\.40$/);assert.match(formatUnitRate(2.1900000000000004,'USD'),/2\.19$/);
 assert.match(formatUnitRate(.000000001,'USD'),/0\.000000001$/);assert.equal(formatUnitRate(null,'CNY'),'未知');
});
