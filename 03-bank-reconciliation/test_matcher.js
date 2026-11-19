const fs=require('fs');const {reconcile}=require('./matcher.js');
const parse=t=>{const [h,...r]=t.trim().split(/\r?\n/);const k=h.split(',');return r.map(l=>{const v=l.split(',');return Object.fromEntries(k.map((x,i)=>[x,v[i]]));});};
const bank=parse(fs.readFileSync(__dirname+'/bank.csv','utf8')),ledger=parse(fs.readFileSync(__dirname+'/ledger.csv','utf8'));
const truth=parse(fs.readFileSync(__dirname+'/ground_truth.csv','utf8'));
const t0=Date.now();const r=reconcile(bank,ledger);const ms=Date.now()-t0;
const tm=Object.fromEntries(truth.map(t=>[t.bank_id,t]));
let correct=0,wrong=0;
r.matched.forEach(m=>{const t=tm[m.bank.id];(t&&t.ledger_id===m.ledger.id)?correct++:wrong++;});
const excHit=r.exceptions.filter(e=>{const t=tm[e.bank.id];return t&&t.expected==='exception'&&e.candidates.some(c=>c.id===t.ledger_id);}).length;
console.log(JSON.stringify({bank_rows:bank.length,ledger_rows:ledger.length,auto_matched:r.matched.length,correct_matches:correct,wrong_matches:wrong,
 expected_matches:truth.filter(t=>t.expected==='match').length,match_rate_pct:+(100*correct/bank.length).toFixed(1),precision_pct:+(100*correct/r.matched.length).toFixed(1),
 low_confidence_flagged:r.matched.filter(m=>m.confidence==='review').length,unmatched_bank:r.unmatchedBank.length,unmatched_ledger:r.unmatchedLedger.length,
 fee_exceptions_with_correct_candidate:excHit,runtime_ms:ms},null,1));
