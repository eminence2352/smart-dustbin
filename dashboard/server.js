import express from 'express';
import { createStore } from './store.js';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root=path.dirname(fileURLToPath(import.meta.url));
export function createApp(store=createStore(path.join(root,'smartbin.db'))){
 const app=express();store.seed();let running=true;
 app.use(express.json({limit:'16kb'}));
 app.use('/fonts/manrope',express.static(path.join(root,'node_modules/@fontsource-variable/manrope/files')));
 app.use('/fonts/space',express.static(path.join(root,'node_modules/@fontsource-variable/space-grotesk/files')));
 app.use(express.static(path.join(root,'public')));
 app.use('/api',(req,res,next)=>{res.set('Cache-Control','no-store');next();});
 app.get('/api/bins',(req,res)=>res.json({bins:store.all().map(b=>store.view(b)),running,serverTime:Date.now()}));
 app.get('/api/bins/:id',(req,res)=>{const b=store.get(req.params.id);if(!b)return res.status(404).json({error:'Bin not found.'});res.json({...store.view(b),readings:store.history(b.id),collections:store.collections(b.id)});});
 app.get('/api/bins/:id/readings',(req,res)=>res.json(store.history(req.params.id,Math.max(1,Math.min(500,Number(req.query.limit)||200)))));
 app.get('/api/bins/:id/collections',(req,res)=>res.json(store.collections(req.params.id)));
 app.get('/api/collections',(req,res)=>res.json(store.collections()));
 app.post('/api/readings',(req,res)=>res.json(store.ingest(req.body)));
 app.post('/api/bins/:id/collect',(req,res)=>res.json(store.collect(req.params.id,req.body.requestId)));
 app.post('/api/demo/simulation',(req,res)=>{if(typeof req.body.running!=='boolean')return res.status(400).json({error:'Choose running or paused.'});running=req.body.running;res.json({running});});
 app.post('/api/demo/bins/:id',(req,res)=>{const b=store.get(req.params.id);if(!b)return res.status(404).json({error:'Bin not found.'});if(typeof req.body.paused!=='boolean')return res.status(400).json({error:'Invalid pause setting.'});b.paused=req.body.paused;store.save(b);res.json({ok:true});});
 app.use((err,req,res,next)=>{console.error(err.message);res.status(err.status||500).json({error:err.status?err.message:'Could not save this update. Please try again.'});});
 return {app,store,isRunning:()=>running};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 const {app,store,isRunning}=createApp();const port=Number(process.env.PORT)||3000;
 const server=app.listen(port,'0.0.0.0',()=>console.log(`Smart Dustbin is ready: http://localhost:${port}`));
 let busy=false;
 const timer=setInterval(async()=>{
  if(!isRunning()||busy)return;busy=true;
  try {for(const b of store.all()){
   if(b.paused)continue;
   const f=b.fill??10;
   // Keep a stable low period after a full bin so collection detection can settle.
   const next=f>=99?6:Math.min(100,f+(f<10?.25:.08+Math.random()*.2));
   await fetch(`http://127.0.0.1:${port}/api/readings`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({binId:b.id,distanceCm:+(40-next*.35).toFixed(2),tempC:+(28+Math.random()*2).toFixed(1),humidity:Math.round(58+Math.random()*8),opensDelta:Math.random()>.8?1:0,requestId:crypto.randomUUID()})});
  }}catch(e){console.error('Simulation update:',e.message);}finally{busy=false;}
 },5000);
 process.on('SIGINT',()=>{clearInterval(timer);server.close(()=>{store.db.close();process.exit();});});
}
