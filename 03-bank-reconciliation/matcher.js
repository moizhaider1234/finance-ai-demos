// Fuzzy bank <-> ledger matcher. Pure function; pasted verbatim into the n8n Code node.
function norm(s){return String(s||'').toLowerCase().replace(/[^a-z0-9 ]/g,' ').replace(/\b(pos|purchase|card|payment|pmt|ref|ach|dd|fpi|bacs|inv|the|ltd|inc|llc)\b/g,' ').replace(/\s+/g,' ').trim();}
function tokens(s){return norm(s).split(' ').filter(t=>t.length>2);}
function sim(a,b){const A=tokens(a),B=tokens(b);if(!A.length||!B.length)return 0;let hit=0;for(const t of A){if(B.some(u=>u===t||(t.length>=4&&u.length>=4&&(u.startsWith(t.slice(0,4))))))hit++;}return hit/(A.length+B.length-hit);}
function days(a,b){return Math.abs((new Date(a)-new Date(b))/86400000);}
function reconcile(bank,ledger,opts){
  const win=(opts&&opts.window)||3, tol=(opts&&opts.tol)||0.005;
  const pairs=[];
  bank.forEach((b,i)=>ledger.forEach((l,j)=>{
    if(Math.abs(Number(b.amount)-Number(l.amount))<=tol){const d=days(b.date,l.date);
      if(d<=win){const s=sim(b.description,l.memo);pairs.push({i,j,score:0.6*s+0.4*(1-d/(win+1)),sim:s,d});}}
  }));
  const cb={},cl={};pairs.forEach(p=>{cb[p.i]=(cb[p.i]||0)+1;cl[p.j]=(cl[p.j]||0)+1;});
  pairs.sort((x,y)=>y.score-x.score);
  const ub=new Set(), ul=new Set(), matched=[];
  for(const p of pairs){ if(ub.has(p.i)||ul.has(p.j))continue; ub.add(p.i); ul.add(p.j);
    matched.push({bank:bank[p.i],ledger:ledger[p.j],score:+p.score.toFixed(3),confidence:(cb[p.i]>1||cl[p.j]>1)?'review':'high'});}
  const unB=bank.filter((_,i)=>!ub.has(i)), unL=ledger.filter((_,j)=>!ul.has(j));
  const exceptions=unB.map(b=>{
    const cands=unL.map(l=>{const rel=Math.abs(Number(b.amount)-Number(l.amount))/Math.max(1,Math.abs(Number(b.amount)));
      return {l,rel,d:days(b.date,l.date),s:sim(b.description,l.memo)};})
      .filter(c=>c.d<=10&&(c.rel<=0.05||c.s>=0.3))
      .sort((x,y)=>(y.s-x.s)||(x.rel-y.rel)).slice(0,3).map(c=>c.l);
    return {bank:b,candidates:cands};});
  return {matched,unmatchedBank:unB,unmatchedLedger:unL,exceptions};
}
if(typeof module!=='undefined')module.exports={reconcile,sim};
