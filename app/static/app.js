const $ = id => document.getElementById(id);
let assets = [];
const today = new Date();
$('date').value = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
function message(text, error=false) { $('message').textContent=text; $('message').classList.toggle('error',error); }
async function api(url,options) { const r=await fetch(url,options); const data=await r.json(); if(!r.ok) throw new Error(typeof data.detail==='string'?data.detail:'Revisa los parámetros de entrada.'); return data; }
function cell(text) { const td=document.createElement('td'); td.textContent=text; return td; }
function drawAssets() {
  const query=$('search').value.toLocaleLowerCase();
  const rows=assets.filter(a=>[a.asset_id,a.name,a.category].some(v=>v.toLocaleLowerCase().includes(query)));
  $('assets').replaceChildren(); $('count').textContent=rows.length;
  if(!rows.length) { const tr=document.createElement('tr'),td=cell('No hay equipos para estos filtros.'); td.colSpan=5; tr.append(td); $('assets').append(tr); }
  for(const a of rows) {
    const tr=document.createElement('tr'),name=cell(a.name),small=document.createElement('small'); small.textContent=`${a.asset_id} · ${a.category}`; name.append(small);
    const status=cell(''),badge=document.createElement('span'); badge.className=`badge ${a.status}`; badge.textContent=a.status; status.append(badge);
    tr.append(name,cell(a.location),cell(a.criticality),cell(a.due_date),status); $('assets').append(tr);
  }
}
async function refresh() {
  if(!$('date').value) { message('Selecciona una fecha de corte.',true); return; }
  const params=new URLSearchParams({as_of:$('date').value}); if($('location').value) params.set('location',$('location').value);
  const data=await api(`/api/dashboard?${params}`),m=data.metrics; assets=data.assets;
  const selected=$('location').value; $('location').replaceChildren(new Option('Todas las sedes',''),...data.locations.map(l=>new Option(l,l))); $('location').value=selected;
  for(const key of ['total','overdue','upcoming']) $(key).textContent=m[key];
  $('critical').textContent=m.critical_overdue; $('compliance').textContent=m.compliance===null?'—':`${m.compliance}%`;
  $('export').href=`/api/export?${params}`; $('bars').replaceChildren();
  for(const [label,value,color] of [['Al día',m.current,'#749b65'],['Próximo',m.upcoming,'#d7b757'],['Vencido',m.overdue,'#c9866b'],['Sin historial',m.unknown,'#a0aaa2']]) {
    const row=document.createElement('div'); row.className='bar-row'; const name=document.createElement('span');name.textContent=label;
    const track=document.createElement('div');track.className='bar-track'; const fill=document.createElement('div');fill.className='bar-fill';fill.style.width=`${m.total?100*value/m.total:0}%`;fill.style.background=color;track.append(fill);
    const n=document.createElement('span');n.textContent=value;row.append(name,track,n);$('bars').append(row);
  }
  $('insight-title').textContent=m.overdue?`${m.overdue} equipos necesitan atención.`:m.total?'Tu plan está al día.':'Prepara tu siguiente intervención.';
  $('insight').textContent=m.total?`${m.critical_overdue} equipos críticos vencidos y ${m.upcoming} servicios próximos. Revisa el inventario para planear intervenciones.${m.unknown?' '+m.unknown+' equipos tienen servicio posterior al corte y se excluyen del cumplimiento.':''}`:'Carga los datos de demostración o un CSV con el esquema documentado.';
  drawAssets(); await refreshRuns();
}
async function refreshRuns() {
  const runs=await api('/api/runs'); $('runs').replaceChildren();
  if(!runs.length) $('runs').textContent='Todavía no hay cargas.';
  for(const r of runs) { const div=document.createElement('div');div.className='run'; const title=document.createElement('strong');title.textContent=`Carga #${r.id} · ${new Date(r.created_at).toLocaleString('es-CO')}`;
    const detail=document.createElement('div');detail.textContent=`${r.inserted} nuevos · ${r.updated} actualizados · ${r.unchanged} sin cambios · ${r.rejected} rechazados`;div.append(title,detail);
    if(r.errors.length) {const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Ver filas rechazadas';details.append(summary);for(const e of r.errors){const p=document.createElement('p');p.textContent=`Fila ${e.row_number}: ${e.reason}`;details.append(p);}div.append(details);} $('runs').append(div);
  }
}
async function load(action) { $('demo').disabled=true; try { const r=await action(); await refresh(); message(`Carga #${r.run_id}: ${r.inserted} nuevos, ${r.updated} actualizados, ${r.unchanged} sin cambios, ${r.rejected} rechazados.`); } catch(e) {message(e.message,true);} finally {$('demo').disabled=false;} }
$('demo').onclick=()=>load(()=>api('/api/demo',{method:'POST'}));
$('upload').onchange=async e=>{const file=e.target.files[0]; if(!file)return; if(file.size>2000000){message('El CSV supera el límite de 2 MB.',true);e.target.value='';return;} await load(async()=>api('/api/import',{method:'POST',headers:{'Content-Type':'text/csv'},body:await file.text()}));e.target.value='';};
for(const id of ['date','location']) $(id).onchange=()=>refresh().catch(e=>message(e.message,true));
$('search').oninput=drawAssets;
refresh().catch(e=>message(e.message,true));
