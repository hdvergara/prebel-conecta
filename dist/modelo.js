const Modelo = (() => {
  const clave = 'prebel-conecta-v2';
  const perfiles = [...catalogo.personas, {
    id:'laura', nombre:'Laura Gómez', cargo:'Gestora de atención', area:'gh', rol:'gestor'
  }];
  const cerrados = ['Resuelto','Cancelada','Devuelta'];
  const ahora = () => new Date().toISOString();
  const fecha = date => {
    const d = date || new Date();
    return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');
  };
  const normalizar = text => text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
  const evento = (autor, texto, estado) => ({autor,texto,estado,fecha:ahora()});
  const inicial = () => ({
    version:2, revision:0, siguiente:1004, articulos:structuredClone(conocimientoInicial), borradores:{}, feedback:[],
    casos:[
      {id:'PC-1001',persona:'valentina',tipo:'Consulta',tema:'Nómina',asunto:'Revisar concepto del comprobante',estado:'En atención',creado:ahora(),ejemplo:true,
        historial:[evento('valentina','Quiero entender el concepto de ajuste de mi comprobante.','Recibido'),evento('laura','Estamos revisando el período de ejemplo.','En atención')]},
      {id:'PC-1002',persona:'mateo',tipo:'Consulta',tema:'SST',asunto:'Consulta de reposición de gafas',estado:'Esperando información',creado:ahora(),ejemplo:true,
        historial:[evento('mateo','Quisiera consultar la reposición de mis gafas.','Recibido'),evento('laura','Indica tu sede y turno de demostración para continuar.','Esperando información')]},
      {id:'PC-1003',persona:'valentina',tipo:'Consulta',tema:'Contratación',asunto:'Certificado sin salario',estado:'Resuelto',creado:ahora(),ejemplo:true,
        historial:[evento('valentina','¿Puedo generar una constancia sin salario?','Recibido'),evento('laura','Sí. En Certificados selecciona Sin salario y revisa la vista previa.','Resuelto')]}
    ]
  });
  function migrar(storage) {
    const state = inicial();
    for (const p of catalogo.personas) {
      let anteriores;
      try { anteriores = JSON.parse(storage.getItem(p.id==='valentina'?'prebel-demo-v1':'prebel-demo-v1-'+p.id) || '[]'); } catch { continue; }
      if (!Array.isArray(anteriores)) continue;
      for (const old of anteriores) {
        if (!old || !['Vacaciones','Certificado laboral'].includes(old.kind)) continue;
        if (old.kind==='Vacaciones' && (!/^\d{4}-\d{2}-\d{2}$/.test(old.start) || !/^\d{4}-\d{2}-\d{2}$/.test(old.end) || !Number.isFinite(old.days) || old.days<=0)) continue;
        state.casos.unshift({
          id:'PC-'+state.siguiente++, persona:p.id, tipo:old.kind,
          tema:old.kind==='Vacaciones'?'Gestión Humana':'Contratación', asunto:old.kind,
          estado:old.status==='Pendiente'?'Recibido':old.status==='Cancelada'?'Cancelada':'Resuelto',
          inicio:old.start,fin:old.end,dias:old.days,creado:ahora(),
          documento:old.kind==='Certificado laboral'?{titulo:'Certificado laboral',lineas:[String(old.body || '')]}:null,
          historial:[evento(p.id,'Solicitud recuperada de la versión anterior.',old.status)]
        });
      }
    }
    return state;
  }
  function leer(storage=localStorage) {
    const raw=storage.getItem(clave);
    if (!raw) return migrar(storage);
    const state=JSON.parse(raw);
    if (state.version!==2 || !Array.isArray(state.casos) || !Array.isArray(state.articulos)) throw new Error('Los datos guardados no se pudieron abrir. Usa Restablecer demo para recuperar los ejemplos.');
    return state;
  }
  async function guardar(cambio) {
    const apply = () => {
      const state=leer();
      cambio(state);
      state.revision++;
      localStorage.setItem(clave,JSON.stringify(state));
      return state;
    };
    if (typeof navigator!=='undefined' && navigator.locks) return navigator.locks.request(clave,apply);
    return apply();
  }
  const persona = id => perfiles.find(p=>p.id===id);
  const visible = (a,p) => p.rol==='gestor' || a.audiencia==='todos' || a.audiencia===p.area;
  const saldo = (state,id) => persona(id).saldo - state.casos.filter(c=>c.persona===id && c.tipo==='Vacaciones' && !cerrados.includes(c.estado)).reduce((n,c)=>n+c.dias,0);
  function dias(inicio,fin) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(inicio) || !/^\d{4}-\d{2}-\d{2}$/.test(fin)) return 0;
    const from=new Date(inicio+'T12:00:00'), to=new Date(fin+'T12:00:00');
    if (!Number.isFinite(from.getTime()) || !Number.isFinite(to.getTime()) || fecha(from)!==inicio || fecha(to)!==fin || to-from>732*86400000) return 0;
    let count=0;
    for(let day=new Date(inicio+'T12:00:00');day<=new Date(fin+'T12:00:00');day.setDate(day.getDate()+1)) {
      if(day.getDay()%6!==0) count++;
    }
    return count;
  }
  function crearCaso(state,id,datos) {
    if (!persona(id) || persona(id).rol==='gestor') throw new Error('Selecciona un colaborador para crear una solicitud.');
    if (datos.tipo==='Vacaciones') {
      if (datos.inicio<fecha() || datos.fin<datos.inicio || datos.fin.slice(0,4)>String(new Date().getFullYear()+2)) throw new Error('Revisa las fechas. Elige un período futuro dentro de los próximos dos años.');
      datos.dias=dias(datos.inicio,datos.fin);
      if (!datos.dias || datos.dias>saldo(state,id)) throw new Error('El período debe incluir días hábiles y estar dentro de tu saldo disponible.');
      const overlap=state.casos.some(c=>c.persona===id && c.tipo==='Vacaciones' && !cerrados.includes(c.estado) && c.inicio<=datos.fin && c.fin>=datos.inicio);
      if (overlap) throw new Error('Ya existe una solicitud activa para esas fechas.');
    }
    const caso={...datos,id:'PC-'+state.siguiente++,persona:id,estado:datos.documento?'Resuelto':'Recibido',creado:ahora()};
    caso.historial=[evento(id,datos.mensaje || 'Solicitud registrada.',caso.estado)];
    state.casos.unshift(caso);
    return caso;
  }
  function actualizarCaso(state,actor,id,estado,texto) {
    const c=state.casos.find(c=>c.id===id), p=persona(actor);
    if (!c || !p || (p.rol!=='gestor' && c.persona!==actor)) throw new Error('No puedes consultar este caso.');
    if (cerrados.includes(c.estado) || c.estado==='Aprobada') throw new Error('Este caso ya tiene una decisión final.');
    const permitidos=p.rol==='gestor'
      ? ['En atención','Esperando información',...(c.tipo==='Vacaciones'?['Aprobada','Devuelta']:['Resuelto'])]
      : ['Cancelada',...(c.estado==='Esperando información'?['Recibido']:[])];
    if (!permitidos.includes(estado)) throw new Error('El cambio de estado no está disponible.');
    if (!texto.trim()) throw new Error('Escribe una respuesta antes de continuar.');
    c.estado=estado;
    c.historial.push(evento(actor,texto.trim(),estado));
  }
  function buscar(state,p,consulta) {
    const words=normalizar(consulta).split(/\W+/).filter(w=>w.length>2 && !['como','para','quiero','necesito','tengo','una','mis','los','las','del','que','por','con'].includes(w));
    return state.articulos.filter(a=>visible(a,p)).map(a=>{
      const keys=normalizar(a.titulo+' '+a.palabras).split(/\W+/);
      return {articulo:a,score:words.filter(w=>keys.some(k=>k.startsWith(w))).length};
    }).filter(r=>r.score>0).sort((a,b)=>b.score-a.score).slice(0,4).map(r=>r.articulo);
  }
  function publicar(state,id,actor) {
    if (persona(actor)?.rol!=='gestor') throw new Error('Se requiere el perfil de Gestión Humana.');
    const a=state.articulos.find(a=>a.id===id), draft=state.borradores[id];
    if (!a || !draft || !draft.titulo.trim() || !draft.respuesta.trim()) throw new Error('Completa la pregunta y la respuesta.');
    Object.assign(a,draft,{version:a.version+1,actualizado:fecha()});
    delete state.borradores[id];
  }
  return {clave,perfiles,persona,inicial,leer,guardar,fecha,visible,saldo,dias,crearCaso,actualizarCaso,buscar,publicar,normalizar,cerrados};
})();
