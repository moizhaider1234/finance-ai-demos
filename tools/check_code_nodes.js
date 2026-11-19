// Syntax-checks every Code node in every workflow and runs functional smoke tests with mocked n8n globals.
const fs=require('fs'),path=require('path');
const root=path.join(__dirname,'..');
const wfs=fs.readdirSync(root).filter(d=>/^\d\d-/.test(d)).map(d=>path.join(root,d,'workflow.json'));
const get=(wf,name)=>wf.nodes.find(n=>n.name===name).parameters.jsCode;
let bad=0;
for(const p of wfs){const wf=JSON.parse(fs.readFileSync(p));
  for(const n of wf.nodes.filter(n=>n.type==='n8n-nodes-base.code')){
    try{new Function('$json','$input','$',`"use strict";return (()=>{${n.parameters.jsCode}\n})()`);}catch(e){bad++;console.log('SYNTAX ERROR',p,n.name,e.message);}}}
console.log(bad?`${bad} syntax errors`:'all code nodes parse OK');
const run=(js,ctx)=>new Function('$json','$input','$',`return (()=>{${js}\n})()`)(ctx.json,ctx.input,ctx.dollar);
// 02 chaser
{const wf=JSON.parse(fs.readFileSync(path.join(root,'02-overdue-invoice-chaser/workflow.json')));
 const csv=fs.readFileSync(path.join(root,'02-overdue-invoice-chaser/invoices.csv'),'utf8').trim().split('\n');const k=csv[0].split(',');
 const items=csv.slice(1).map(l=>({json:Object.fromEntries(l.split(',').map((v,i)=>[k[i],v]))}));
 // freeze "today" to the demo date used when the CSV was generated
 const RealDate=Date;global.Date=class extends RealDate{constructor(...a){a.length?super(...a):super('2026-11-19T10:00:00');}};
 const out=run(get(wf,'Decide tier + write email'),{input:{all:()=>items}});global.Date=RealDate;
 console.log('02 chaser: invoices in sheet',items.length,'| emails drafted',out.length,'| tiers',out.map(o=>o.json.tier).join(','));
 console.log('   sample:',out[0].json.subject);console.log('   UK sample:',out.find(o=>/\u00a3/.test(o.json.message)).json.subject);}
// 07 scoring
{const wf=JSON.parse(fs.readFileSync(path.join(root,'07-audit-lead-magnet/workflow.json')));
 const r=run(get(wf,'Score + personalise'),{json:{Name:'Test',Email:'t@x.example','Invoices and receipts are entered by hand':'Always','Bank reconciliation takes more than a day each month':'Sometimes','Overdue invoices are chased manually':'Always'}});
 console.log('07 scoring:',r.json.score,r.json.tier,'| actions',r.json.actions.map(a=>a.area).join(', '));}
// 06 calc
{const wf=JSON.parse(fs.readFileSync(path.join(root,'06-monthly-report-generator/workflow.json')));
 const csv=fs.readFileSync(path.join(root,'06-monthly-report-generator/figures.csv'),'utf8').trim().split('\n');const k=csv[0].split(',');
 const items=csv.slice(1).map(l=>({json:Object.fromEntries(l.split(',').map((v,i)=>[k[i],v]))}));
 const r=run(get(wf,'Calculate'),{input:{all:()=>items}})[0];console.log("06 calc: month",r.json.cur.month,"revenue",r.json.cur.revenue,"net",r.json.cur.net_profit,"margin",(r.json.cur.margin*100).toFixed(1)+"%","MoM rev",r.json.mom.revenue_pct.toFixed(1)+"%");
}
