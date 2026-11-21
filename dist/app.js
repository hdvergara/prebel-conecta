const $ = id => document.getElementById(id);
const services = [
  ['vacaciones','Vacaciones','Planea tu descanso','☼','#f6dfbc'],
  ['nomina','Nómina','Consulta tu comprobante','▤','#e5e4f2'],
  ['certificado','Certificados','Genera tu constancia','✎','#f4ddd7'],
  ['solicitudes','Mis solicitudes','Revisa tus trámites','◷','#dceade']
];
const intents = [
  ['saldo','Ver mi saldo','vacaciones descanso cuantos dias disponibles saldo'],
  ['prediccion','Proyectar saldo','prediccion futuro proyectar cuanto tendre acumular simulacion'],
  ['vacaciones','Pedir vacaciones','solicitar vacaciones pedir descanso fechas'],
  ['nomina','Consultar nómina','pago salario nomina comprobante desprendible'],
  ['certificado','Generar certificado','carta certificado laboral constancia'],
  ['solicitudes','Seguir mi solicitud','estado seguimiento solicitudes historial pendiente']
];
const perfil = $('perfil');
for (const persona of catalogo.personas) perfil.add(new Option(persona.nombre, persona.id));
try { perfil.value = localStorage.getItem('perfil-demo') || 'valentina'; } catch {}
const persona = catalogo.personas.find(p => p.id === perfil.value) || catalogo.personas[0];
perfil.value = persona.id;
const area = id => catalogo.areas.find(a => a.id === id).nombre;
$('nombre').textContent = persona.nombre.split(' ')[0];
$('puesto').textContent = persona.cargo + ' · ' + area(persona.area);
const recursos = catalogo.recursos.filter(r => !r.audiencia || r.audiencia === persona.area);
for (const recurso of recursos) {
  const owner = area(recurso.responsable);
  const card = services.find(s => s[0] === recurso.id);
  if (card) card[2] += ' · ' + owner;
  else services.push([recurso.id,recurso.titulo,owner,'✚','#e2ebed']);
  const intent = intents.find(i => i[0] === recurso.id);
  const tags = normalizeCatalog(owner + ' ' + recurso.palabras);
  if (intent) intent[2] += ' ' + tags;
  else intents.push([recurso.id,recurso.titulo,tags]);
}
function ownerLabel(areaId) {
  if (!areaId) return null;
  const info = catalogo.areas.find(a => a.id === areaId);
  return info.padre ? area(info.padre) + ' · ' + info.nombre : info.nombre;
}
const preguntas = [
  {id:'faq-saldo', ruta:'saldo', titulo:'¿Dónde veo cuántos días de vacaciones tengo?', respuesta:'En Mi saldo de vacaciones aparecen tus días disponibles. Si tienes una solicitud pendiente, esos días ya están reservados.', enlace:'Ver mi saldo'},
  {id:'faq-prediccion', ruta:'prediccion', titulo:'¿Cuántos días de vacaciones tendré en unos meses?', respuesta:'Elige un plazo para estimar tu saldo futuro. La demo suma 1,25 días por mes a tu saldo disponible y supone que no tomarás más vacaciones durante ese período.', enlace:'Proyectar mi saldo'},
  {id:'faq-nomina', ruta:'nomina', titulo:'¿Cómo descargo mi comprobante de pago?', respuesta:'Abre Nómina, elige uno de los tres períodos disponibles y pulsa Descargar comprobante.', enlace:'Abrir Nómina'},
  {id:'faq-certificado', ruta:'certificado', titulo:'¿Puedo pedir un certificado laboral con salario?', respuesta:'Sí. En Certificados, elige Con salario o Sin salario antes de generarlo. Luego puedes descargarlo desde Mis solicitudes.', enlace:'Generar certificado'}
];
for (const recurso of recursos.filter(r => r.contenido)) {
  const titulos = {dotacion:'¿Cómo pido el cambio de mis guantes o gafas?', ergonomia:'¿Cómo solicito una revisión de mi puesto de oficina?'};
  if (titulos[recurso.id]) preguntas.push({id:'faq-'+recurso.id, ruta:recurso.id, titulo:titulos[recurso.id], respuesta:recurso.contenido, enlace:recurso.titulo});
}
const enlacesModelo = {vacaciones:'Planear vacaciones', nomina:'Abrir Nómina', certificado:'Generar certificado'};
faqModel.faq.forEach((item,i) => {
  preguntas.push({id:'faq-modelo-'+i, ruta:item.ruta, titulo:item.preguntas[0], respuesta:item.respuesta, enlace:item.ruta && enlacesModelo[item.ruta], area:item.area, palabras:item.preguntas.join(' ')});
});
intents.push(['preguntas','Preguntas frecuentes','preguntas frecuentes faq ayuda dudas']);
for (const pregunta of preguntas) {
  const item = document.createElement('details');
  item.id = pregunta.id;
  const summary = document.createElement('summary');
  summary.textContent = pregunta.titulo;
  const answer = document.createElement('p');
  answer.textContent = pregunta.respuesta;
  item.append(summary, answer);
  const owner = ownerLabel(pregunta.area);
  if (owner) {
    const tag = document.createElement('p');
    tag.className = 'muted';
    tag.textContent = owner;
    item.append(tag);
  }
  if (pregunta.ruta) {
    const link = document.createElement('a');
    link.href = '#' + pregunta.ruta;
    link.textContent = pregunta.enlace + ' →';
    item.append(link);
  }
  $('faq-list').append(item);
  intents.push([pregunta.id,pregunta.titulo,normalizeCatalog(pregunta.palabras || pregunta.titulo)]);
}
function normalizeCatalog(text) { return text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,''); }
const key = persona.id === 'valentina' ? 'prebel-demo-v1' : 'prebel-demo-v1-' + persona.id;
let requests = [];
try { requests = JSON.parse(localStorage.getItem(key) || '[]'); } catch {}
if (!Array.isArray(requests)) requests = [];
perfil.onchange = () => {
  try {localStorage.setItem('perfil-demo',perfil.value);} catch {}
  location.reload();
};
const available = () => persona.saldo - requests.reduce((n,r) => n + (r.kind === 'Vacaciones' && r.status === 'Pendiente' ? r.days : 0),0);
const modal = $('modal'), detail = $('detail');
const today = new Date();
const iso = date => [date.getFullYear(),String(date.getMonth()+1).padStart(2,'0'),String(date.getDate()).padStart(2,'0')].join('-');
const dateLabel = s => new Date(s+'T12:00:00').toLocaleDateString('es-CO',{day:'numeric',month:'short',year:'numeric'});
const normalize = text => normalizeCatalog(text);
const token = () => crypto.randomUUID ? crypto.randomUUID() : String(Date.now());
function save() {
  try {localStorage.setItem(key,JSON.stringify(requests));} catch {}
  $('balance').textContent = available();
}
function rank(text) {
  const words = normalize(text).split(/\W+/).filter(w=>w.length>2 && !['que','los','las','del','mis','una','por','con','tengo'].includes(w));
  return intents.map(([id,label,keys])=>({id,label,score:words.filter(w=>keys.split(' ').some(k=>k.startsWith(w))).length})).filter(row=>row.score).sort((a,b)=>b.score-a.score);
}
function suggestions() {
  const ranked = rank($('query').value);
  const options = $('query').value.trim() ? ranked.slice(0,3) : [
    ...intents.slice(0,2).map(([id,label])=>({id,label})),
    {id:'nomina', label:'¿Cómo descargo mi comprobante de nómina?'},
    {id:'certificado', label:'¿Cómo obtengo mi certificado laboral?'}
  ];
  $('matches').innerHTML = options.length ? options.map(o=>'<button class="chip" data-route="'+o.id+'">'+o.label+' →</button>').join('') : '<p class="muted">Sin coincidencias. Prueba con “vacaciones”, “pago” o “certificado”.</p>';
}
function show(title,body) {
  detail.innerHTML='<h2 id="dialog-title">'+title+'</h2>'+body;
  modal.setAttribute('aria-labelledby','dialog-title');
  if(!modal.open) modal.showModal();
}
function action(route,label){return '<button class="primary" data-route="'+route+'">'+label+'</button>';}
const MODEL_API = 'http://127.0.0.1:5000/reply';
function escapeHtml(text) { return text.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function modelReply(text) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 1500);
  return fetch(MODEL_API, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text}), signal: controller.signal})
    .then(r => r.ok ? r.json() : Promise.reject())
    .catch(() => ({reply: faqModel.fallback, ruta: null, area: null, confianza: null, sentimiento: null}))
    .finally(() => clearTimeout(timeout));
}
function sentimentLabel(s) {
  if (!s) return 'No disponible (API local no activa)';
  const emoji = {negativo:'😟', neutral:'😐', positivo:'🙂'}[s.etiqueta] || '';
  return emoji+' '+s.etiqueta+' · '+Math.round(s.confianza*100)+'%';
}
function askAssistant(text) {
  if (!text) return;
  const box = $('model-box');
  box.hidden = false;
  $('model-query').textContent = text;
  const quick = rank(text)[0];
  $('model-quick').textContent = quick ? quick.label : 'Sin coincidencia rápida';
  $('model-answer').textContent = 'Consultando…';
  $('model-confidence').textContent = '—';
  $('model-sentiment').textContent = '—';
  $('model-owner').textContent = '';
  $('model-action').innerHTML = '';
  box.scrollIntoView({block:'center', behavior:'smooth'});
  modelReply(text).then(({reply,ruta,area,confianza,sentimiento}) => {
    $('model-answer').textContent = reply;
    $('model-confidence').textContent = confianza != null ? Math.round(confianza*100)+'%' : 'No disponible (API local no activa)';
    $('model-sentiment').textContent = sentimentLabel(sentimiento);
    $('model-owner').textContent = ownerLabel(area) || '';
    $('model-action').innerHTML = ruta ? action(ruta, enlacesModelo[ruta] || 'Ir a la sección') : '';
  });
}
function weekdays(start,end){
  let count=0;
  for(let day=new Date(start+'T12:00:00');day<=new Date(end+'T12:00:00');day.setDate(day.getDate()+1)){
    if(day.getDay()%6!==0) count++;
  }
  return count;
}
function vacation(start='',end=''){
  show('Planear vacaciones','<p>Dispones de <b>'+available()+' días</b>. Para esta demo contamos de lunes a viernes, incluidos los festivos.</p><form id="dates"><label for="start">Desde</label><input type="date" id="start" required><label for="end">Hasta</label><input type="date" id="end" required><p id="error" class="error" role="alert"></p><button class="primary">Revisar solicitud</button></form>');
  $('start').min=iso(today); $('start').value=start; $('end').min=start||iso(today); $('end').value=end;
  $('start').oninput=()=>{$('end').min=$('start').value||iso(today);};
  $('dates').onsubmit=e=>{
    e.preventDefault();
    const a=$('start').value,b=$('end').value,days=weekdays(a,b);
    const overlap=requests.some(r=>r.kind==='Vacaciones' && r.status==='Pendiente' && r.start<=b && r.end>=a);
    const error=overlap?'Ya tienes una solicitud para esas fechas.':!days?'Elige al menos un día de lunes a viernes.':days>available()?'Los días solicitados superan tu saldo disponible.':'';
    if(error){$('error').textContent=error;return;}
    show('Revisar solicitud','<p>'+dateLabel(a)+' — '+dateLabel(b)+'</p><p class="status">'+days+' días hábiles · Saldo restante: '+(available()-days)+'</p><button class="chip" id="edit">Editar fechas</button> <button class="primary" id="send">Confirmar solicitud</button>');
    $('edit').onclick=()=>vacation(a,b);
    $('send').onclick=()=>{
      requests.unshift({id:token(),kind:'Vacaciones',start:a,end:b,days,status:'Pendiente'});save();
      show('Solicitud registrada','<p>Tu solicitud de '+days+' días quedó pendiente de aprobación en la demo.</p>'+action('solicitudes','Ver mis solicitudes'));
    };
  };
}
function forecast(){
  show('Proyectar mi saldo','<p>Elige cuántos meses quieres proyectar. La simulación suma 1,25 días por mes a tu saldo disponible.</p><label for="months">Horizonte de la consulta</label><select id="months">'+[1,3,6,12].map(n=>'<option value="'+n+'">'+n+(n===1?' mes':' meses')+'</option>').join('')+'</select><p id="estimate" class="status" aria-live="polite"></p>'+action('vacaciones','Planear vacaciones'));
  const update=()=>{$('estimate').textContent='Saldo estimado: '+(available()+1.25*Number($('months').value)).toLocaleString('es-CO')+' días. Supone que no pedirás más vacaciones.';};
  $('months').onchange=update;update();
}
function download(filename,body){
  const url=URL.createObjectURL(new Blob(['Prebel Conecta · Documento de demostración\n\n'+body],{type:'text/plain;charset=utf-8'}));
  const link=document.createElement('a');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1500);
}
function payroll(){
  const months=Array.from({length:3},(_,i)=>new Date(today.getFullYear(),today.getMonth()-1-i,1).toLocaleDateString('es-CO',{month:'long',year:'numeric'}));
  show('Comprobante de nómina','<label for="period">Período liquidado</label><select id="period">'+months.map(m=>'<option>'+m+'</option>').join('')+'</select><p>' + persona.nombre + ' · ' + persona.cargo + '</p><div id="pay" class="status" aria-live="polite"></div><button class="primary" id="download">Descargar comprobante (.txt)</button>');
  const summary=()=>{const extra=$('period').selectedIndex*50000;return 'Devengado: $'+(persona.salario+extra).toLocaleString('es-CO')+' COP · Deducciones: $'+(persona.salario*0.08).toLocaleString('es-CO')+' COP · Neto: $'+(persona.salario*0.92+extra).toLocaleString('es-CO')+' COP';};
  const update=()=>{$('pay').textContent=summary();};$('period').onchange=update;update();
  $('download').onclick=()=>download('nomina-demo.txt',persona.nombre+' · '+$('period').value+'\n'+summary());
}
function certificate(){
  show('Certificado laboral','<label for="type">Tipo de certificado</label><select id="type"><option>Sin salario</option><option>Con salario</option></select><p class="muted">Se generará con el perfil ficticio de '+persona.nombre+'.</p><button id="generate" class="primary">Generar certificado</button>');
  $('generate').onclick=()=>{
    const body=persona.nombre+' trabaja como '+persona.cargo.toLowerCase()+' desde el '+dateLabel(persona.ingreso)+'.'+($('type').selectedIndex?' Su salario mensual simulado es de $'+persona.salario.toLocaleString('es-CO')+' COP.':'');
    requests.unshift({id:token(),kind:'Certificado laboral',status:'Generado',body});save();
    show('Certificado generado','<p>'+body+'</p><button id="download" class="primary">Descargar certificado (.txt)</button>');$('download').onclick=()=>download('certificado-demo.txt',body);
  };
}
function historyView(){
  show('Mis solicitudes',requests.length?'':'<p>Aún no tienes solicitudes. Empieza eligiendo tus fechas de descanso.</p>'+action('vacaciones','Solicitar vacaciones'));
  for(const r of requests){
    const row=document.createElement('article');row.className='entry';
    const heading=document.createElement('b');heading.textContent=r.kind+' · '+r.status;row.append(heading);
    if(r.kind==='Vacaciones'){const p=document.createElement('p');p.textContent=dateLabel(r.start)+' — '+dateLabel(r.end)+' · '+r.days+' días';row.append(p);}
    if(r.status==='Pendiente'||r.kind==='Certificado laboral'){
      const btn=document.createElement('button');btn.className='chip';btn.textContent=r.status==='Pendiente'?'Cancelar solicitud':'Descargar certificado';
      btn.onclick=()=>{if(r.kind==='Certificado laboral'){download('certificado-demo.txt',r.body);return;}r.status='Cancelada';save();historyView();};row.append(btn);
    }
    detail.append(row);
  }
}
function route(){
  const pages={vacaciones:vacation,prediccion:forecast,nomina:payroll,solicitudes:historyView,certificado:certificate,saldo:()=>show('Mi saldo de vacaciones','<p class="status">'+available()+' días hábiles disponibles</p><p>Saldo inicial de la demo: '+persona.saldo+' días. Las solicitudes pendientes reservan días hasta que las canceles.</p>'+action('prediccion','Proyectar saldo'))};
  const id = location.hash.slice(1);
  if (id.startsWith('faq-') && preguntas.some(p => id === p.id)) {
    const item = $(id);
    if(modal.open)modal.close();
    item.open = true;
    item.scrollIntoView({block:'center'});
    item.querySelector('summary').focus({preventScroll:true});
    return;
  }
  const resource = catalogo.recursos.find(r => r.id === id);
  if (resource && !recursos.includes(resource)) {
    show('Servicio no disponible','<p>Este servicio está dirigido a otra área.</p>');
    return;
  }
  if (resource?.contenido) {
    show(resource.titulo,'<p class="muted">Gestión Humana · '+area(resource.responsable)+'</p><p>'+resource.contenido+'</p>');
    return;
  }
  const view=pages[location.hash.slice(1)];if(typeof view==='function' && Object.hasOwn(pages,location.hash.slice(1)))view();else if(modal.open)modal.close();
}
$('services').innerHTML=services.map(([id,title,desc,icon,tint])=>'<a class="service" href="#'+id+'" style="--tint:'+tint+'"><em aria-hidden="true">'+icon+'</em><b>'+title+'</b><span>'+desc+'</span></a>').join('');
document.addEventListener('click',event=>{const btn=event.target.closest('[data-route]');if(btn){if(location.hash==='#'+btn.dataset.route)route();else location.hash=btn.dataset.route;}});
$('query').oninput=suggestions;
$('query').onkeydown=e=>{
  if(e.key!=='Enter')return;
  const btn=$('matches').querySelector('button');
  if(btn)btn.click();else askAssistant($('query').value.trim());
};
$('close').onclick=()=>modal.close();
modal.onclose=()=>{if(modal.open || location.hash==='#preguntas' || location.hash.startsWith('#faq-'))return; if(location.hash!=='#inicio')location.hash='inicio';};
window.addEventListener('hashchange',route);
$('balance').textContent=available();suggestions();route();
