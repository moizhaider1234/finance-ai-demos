// Tiny keyword retriever (term-overlap with IDF). Used in the n8n Code node and in test_retrieval.js
const STOP=new Set('the a an and or of to in on for is are do does can i my me you your we our it be how what when which who with at by from that this as if'.split(' '));
const tok=s=>String(s).toLowerCase().replace(/[^a-z0-9 ]/g,' ').split(/\s+/).filter(w=>w.length>2&&!STOP.has(w)).map(w=>w.replace(/(ing|ed|es|s)$/,''));
function retrieve(question,docs,k=3){
  const N=docs.length,df={};docs.forEach(d=>new Set(tok(d.text)).forEach(t=>df[t]=(df[t]||0)+1));
  const q=tok(question);
  return docs.map(d=>{const dt=tok(d.text),c={};dt.forEach(t=>c[t]=(c[t]||0)+1);
    let s=0;q.forEach(t=>{if(c[t])s+=Math.log(1+N/df[t])*(1+Math.log(c[t]));});return {name:d.name,text:d.text,score:s};})
    .sort((a,b)=>b.score-a.score).slice(0,k);
}
if(typeof module!=='undefined')module.exports={retrieve};
