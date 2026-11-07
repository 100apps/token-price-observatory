import{test}from'node:test';import assert from'node:assert/strict';import{calculate,convert}from'../calc.mjs';
test('90% cache, 100m input/output: independently derived invoice',()=>{assert.equal(calculate({input:2,output:8,cache_read:.2},1e8,1e8,.9),838)});
test('unknown cache uses normal input; free cache remains zero',()=>{assert.equal(calculate({input:2,output:8,cache_read:null},1e6,1e6,.9),10);assert.equal(calculate({input:2,output:8,cache_read:0},1e6,0,1),0)});
test('zero usage and currency round trip',()=>{assert.equal(calculate({input:2,output:8},0,0,0),0);assert.ok(Math.abs(convert(convert(123,'USD','CNY',7.2),'CNY','USD',7.2)-123)<1e-9)});
test('missing exchange rate cannot turn USD costs into free CNY prices',()=>{
 assert.ok(Number.isNaN(convert(100,'USD','CNY',null)));assert.ok(Number.isNaN(convert(100,'CNY','USD',0)));assert.equal(convert(100,'CNY','CNY',null),100);
});
