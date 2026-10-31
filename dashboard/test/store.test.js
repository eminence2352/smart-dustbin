import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createStore, fillPercent } from '../store.js';
import { createApp } from '../server.js';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
const raw=(fill,extra={})=>({binId:'bin-01',distanceCm:40-fill*.35,tempC:29,humidity:61,opensDelta:1,...extra});
function setup(){const s=createStore();s.seed();s.collect('bin-01','reset',Date.now()-1000);return s;}
test('calibration and bounds',()=>{assert.equal(fillPercent(19),60);assert.equal(fillPercent(45),0);assert.equal(fillPercent(2),100);assert.equal(fillPercent(null),null);});
test('stable collection occurs once; single outlier does not collect',()=>{const s=setup();try{
 for(let i=0;i<3;i++)s.ingest(raw(75));const count=s.collections('bin-01').length;
 s.ingest(raw(5));s.ingest(raw(75));assert.equal(s.collections('bin-01').length,count);
 for(let i=0;i<3;i++)s.ingest(raw(8));assert.equal(s.collections('bin-01').length,count+1);assert.equal(s.get('bin-01').usesSinceCollection,0);
 for(let i=0;i<5;i++)s.ingest(raw(8));assert.equal(s.collections('bin-01').length,count+1);
}finally{s.db.close();}});
test('null sensors retain last fill but still count openings; duplicate batches are idempotent',()=>{const s=setup();try{
 s.ingest(raw(60));s.ingest(raw(0,{distanceCm:null,tempC:null,humidity:null,opensDelta:3,requestId:'batch-a'}));
 const b=s.get('bin-01');assert.equal(b.fill,60);assert.equal(b.valid,false);assert.equal(b.tempC,null);assert.equal(b.usesSinceCollection,4);
 s.ingest(raw(0,{distanceCm:null,tempC:null,humidity:null,opensDelta:3,requestId:'batch-a'}));assert.equal(s.get('bin-01').usesSinceCollection,4);
}finally{s.db.close();}});
test('manual collection clears high window and does not fabricate empty fill',()=>{const s=setup();try{
 for(let i=0;i<3;i++)s.ingest(raw(80));s.collect('bin-01','manual-action');s.collect('bin-01','manual-action');
 const count=s.collections('bin-01').length;assert.equal(s.get('bin-01').fill,80);assert.equal(s.get('bin-01').usesSinceCollection,0);
 for(let i=0;i<3;i++)s.ingest(raw(6));assert.equal(s.collections('bin-01').length,count);
}finally{s.db.close();}});
test('offline and prediction data requirements',()=>{const s=setup();try{
 const now=Date.now();s.collect('bin-01','prediction',now-1200000);
 for(let i=0;i<15;i++)s.ingest(raw(10+i),now-1200000+i*80000);
 const b=s.get('bin-01');assert.ok(s.view(b,b.lastSeenAt).estimate.at);assert.equal(s.view(b,b.lastSeenAt+30001).online,false);
 s.collect('bin-01','new-cycle');assert.equal(s.view(s.get('bin-01')).estimate.at,null);
}finally{s.db.close();}});
test('invalid data does not mutate state',()=>{const s=setup();try{const before=s.get('bin-01');assert.throws(()=>s.ingest(raw(30,{humidity:101})));assert.throws(()=>s.ingest(raw(30,{opensDelta:-1})));assert.throws(()=>s.ingest(raw(30,{binId:'missing'})),{status:404});assert.deepEqual(s.get('bin-01'),before);}finally{s.db.close();}});
test('SQLite state survives reopening',()=>{const dir=mkdtempSync(path.join(tmpdir(),'smartbin-test-'));const file=path.join(dir,'test.db');try{let s=createStore(file);s.seed();s.ingest(raw(65,{opensDelta:7}));const b=s.get('bin-01');s.db.close();s=createStore(file);assert.deepEqual(s.get('bin-01'),b);s.db.close();}finally{rmSync(dir,{recursive:true,force:true});}});
test('HTTP reading pipeline validates and serves locally bundled assets',async()=>{
 const s=createStore(),{app}=createApp(s);const server=app.listen(0,'127.0.0.1');await new Promise(resolve=>server.once('listening',resolve));const url=`http://127.0.0.1:${server.address().port}`;
 try{let r=await fetch(url+'/api/readings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(raw(50))});assert.equal(r.status,200);assert.equal((await r.json()).fill,50);
 r=await fetch(url+'/api/readings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(raw(50,{binId:'missing'}))});assert.equal(r.status,404);
 r=await fetch(url+'/api/bins/bin-01');assert.equal((await r.json()).fill,50);
 for(const asset of ['/','/app.js','/style.css','/fonts/manrope/manrope-latin-wght-normal.woff2','/fonts/space/space-grotesk-latin-wght-normal.woff2'])assert.equal((await fetch(url+asset)).status,200);
 }finally{await new Promise(resolve=>server.close(resolve));s.db.close();}
});
