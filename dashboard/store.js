import { DatabaseSync } from 'node:sqlite';

export const fillPercent = (d, empty = 40, full = 5) => d === null ? null : Math.round(Math.max(0, Math.min(100, (empty-d)/(empty-full)*100))*10)/10;
export function createStore(path = ':memory:') {
 const db = new DatabaseSync(path);
 db.exec(`PRAGMA journal_mode=WAL; CREATE TABLE IF NOT EXISTS bins(id TEXT PRIMARY KEY, data TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS readings(id INTEGER PRIMARY KEY, bin_id TEXT NOT NULL, ts INTEGER NOT NULL, fill REAL, stable REAL, distance REAL, temp REAL, humidity REAL);
 CREATE INDEX IF NOT EXISTS readings_bin_ts ON readings(bin_id,ts);
 CREATE TABLE IF NOT EXISTS collections(id INTEGER PRIMARY KEY, bin_id TEXT NOT NULL, ts INTEGER NOT NULL, method TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS requests(key TEXT PRIMARY KEY);`);
 const get=id=>{const r=db.prepare('SELECT data FROM bins WHERE id=?').get(id);return r?JSON.parse(r.data):null;};
 const save=b=>db.prepare('INSERT OR REPLACE INTO bins VALUES (?,?)').run(b.id,JSON.stringify(b));
 const all=()=>db.prepare('SELECT data FROM bins ORDER BY id').all().map(r=>JSON.parse(r.data));
 const error=(message,status=400)=>{throw Object.assign(new Error(message),{status});};
 const transact=fn=>{db.exec('BEGIN');try{const result=fn();db.exec('COMMIT');return result;}catch(e){db.exec('ROLLBACK');throw e;}};
 function collectInternal(b,now,method){
  b.lastCollectedAt=now;b.usesSinceCollection=0;b.baseline=null;b.baselineAt=null;b.window=[];b.lastStable=null;
  db.prepare('INSERT INTO collections(bin_id,ts,method) VALUES(?,?,?)').run(b.id,now,method);
 }
 function ingest(p,now=Date.now()) {
  if(!p||typeof p.binId!=='string')error('Choose a registered bin.');
  const b=get(p.binId);if(!b)error('Bin not found.',404);
  for(const [key,min,max] of [['distanceCm',0.01,400],['tempC',0,50],['humidity',0,100]]){
   if(p[key]!==null && (typeof p[key]!=='number'||!Number.isFinite(p[key])||p[key]<min||p[key]>max))error(`${key} must be ${min} to ${max}, or null.`);
  }
  if(!Number.isSafeInteger(p.opensDelta)||p.opensDelta<0||p.opensDelta>10000)error('New openings must be a whole number from 0 to 10000.');
  if(p.requestId!==undefined&&(typeof p.requestId!=='string'||p.requestId.length>100))error('Invalid request identifier.');
  const key=p.requestId?`${b.id}:${p.requestId}`:null;
  if(key&&db.prepare('SELECT key FROM requests WHERE key=?').get(key))return {ok:true,duplicate:true};
  return transact(()=>{
   const fill=fillPercent(p.distanceCm,b.emptyDistance,b.fullDistance);
   b.lastSeenAt=now;b.tempC=p.tempC;b.humidity=p.humidity;b.distanceCm=p.distanceCm;b.valid=fill!==null;b.usesSinceCollection+=p.opensDelta;
   let stable=null, collected=false;
   if(fill!==null){
    b.fill=fill;b.fillAt=now;b.window.push(fill);b.window=b.window.slice(-3);
    if(b.window.length===3&&Math.max(...b.window)-Math.min(...b.window)<=5){
     stable=[...b.window].sort((a,b)=>a-b)[1];
     if(b.lastStable!==null&&b.lastStable>=b.highThreshold&&stable<=b.lowThreshold){collectInternal(b,now,'auto');collected=true;}
     b.lastStable=stable;
     if(b.lastCollectedAt&&b.baseline===null){b.baseline=stable;b.baselineAt=now;}
    }
   }
   db.prepare('INSERT INTO readings(bin_id,ts,fill,stable,distance,temp,humidity) VALUES(?,?,?,?,?,?,?)').run(b.id,now,fill,stable,p.distanceCm,p.tempC,p.humidity);
   if(key)db.prepare('INSERT INTO requests VALUES(?)').run(key);
   save(b);return {ok:true,collected,fill};
  });
 }
 function collect(id,requestId,now=Date.now()){
  const b=get(id);if(!b)error('Bin not found.',404);
  if(typeof requestId!=='string'||!requestId||requestId.length>100)error('An action ID is required.');
  const key=`collect:${id}:${requestId}`;
  if(db.prepare('SELECT key FROM requests WHERE key=?').get(key))return {ok:true,duplicate:true};
  return transact(()=>{collectInternal(b,now,'manual');save(b);db.prepare('INSERT INTO requests VALUES(?)').run(key);return {ok:true};});
 }
 function view(b,now=Date.now()){
  const online=!!b.lastSeenAt&&now-b.lastSeenAt<=30000;
  let estimate={label:'Not enough data yet',at:null};
  if(b.valid&&b.fill>=b.target)estimate={label:'Collect now',at:null};
  else if(b.baselineAt && b.valid && now-b.baselineAt>=600000){
   const pts=db.prepare('SELECT ts,stable FROM readings WHERE bin_id=? AND ts>=? AND stable IS NOT NULL ORDER BY ts').all(b.id,b.baselineAt);
   const last=pts.at(-1);const elapsed=last?last.ts-b.baselineAt:0;const rate=elapsed>0?(last.stable-b.baseline)/elapsed:0;
   if(pts.length>=5&&elapsed>=600000&&rate>0)estimate={label:'Estimated collection',at:Math.round(last.ts+(b.target-last.stable)/rate)};
  }
  if(!online)estimate={...estimate,label:'Offline · last known data'};
  else if(!b.valid)estimate={label:'Waiting for a valid reading',at:null};
  return {...b,online,estimate,source:'simulated'};
 }
 function history(id,limit=200){return db.prepare('SELECT ts,fill FROM readings WHERE bin_id=? ORDER BY ts DESC,id DESC LIMIT ?').all(id,limit).reverse();}
 const collections=id=>id?db.prepare('SELECT * FROM collections WHERE bin_id=? ORDER BY ts DESC,id DESC LIMIT 100').all(id):db.prepare('SELECT * FROM collections ORDER BY ts DESC,id DESC LIMIT 100').all();
 function seed(){
  if(all().length)return;
  const locations=[['Central courtyard','Main courtyard, ground floor'],['Cafeteria entrance','Student cafeteria, east entrance'],['Library corridor','Library building, first floor'],['Academic block','Academic building, ground floor'],['Student common room','Student centre, second floor'],['South gate','South entrance, beside the walkway']];
  const targets=[92,76,43,28,61,35],now=Date.now();
  locations.forEach(([name,address],i)=>{
   const id=`bin-0${i+1}`;save({id,name,address,emptyDistance:40,fullDistance:5,highThreshold:70,lowThreshold:10,target:90,lastCollectedAt:null,usesSinceCollection:0,lastSeenAt:null,fill:null,fillAt:null,tempC:null,humidity:null,distanceCm:null,valid:false,window:[],lastStable:null,baseline:null,baselineAt:null,paused:i===5});
   collect(id,`seed-${i}`,now-3*3600000);
   db.prepare("UPDATE collections SET method='sample' WHERE bin_id=?").run(id);
   for(let k=0;k<=60;k++){const pct=5+(targets[i]-5)*k/60;ingest({binId:id,distanceCm:40-pct*.35,tempC:28+i*.4,humidity:58+i*3,opensDelta:k%4===0?2:0},now-3*3600000+k*3*60000-(i===5?900000:0));}
  });
 }
 return {db,get,save,all,ingest,collect,view,history,collections,seed};
}
