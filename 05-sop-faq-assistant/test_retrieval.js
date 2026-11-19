const fs=require('fs'),path=require('path');const {retrieve}=require('./retriever.js');
const dir=path.join(__dirname,'firm_docs');const docs=fs.readdirSync(dir).sort().map(n=>({name:n,text:fs.readFileSync(path.join(dir,n),'utf8')}));
const rows=fs.readFileSync(path.join(__dirname,'test_questions.csv'),'utf8').trim().split(/\r?\n/).slice(1).map(l=>{const m=l.match(/^(\d+),(.*),(answer|refuse|escalate),(.*)$/);return {id:m[1],q:m[2],exp:m[3],src:m[4]};});
let hit=0,n=0;rows.filter(r=>r.src).forEach(r=>{n++;const top=retrieve(r.q,docs,3).map(d=>d.name);if(top.includes(r.src))hit++;else console.log('MISS',r.id,r.q,top);});
console.log(`retrieval: source doc in top-3 for ${hit}/${n} questions that have a source doc`);
