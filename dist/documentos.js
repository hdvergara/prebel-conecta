const Documentos = (() => {
  const money=n=>'$'+Math.round(n).toLocaleString('es-CO')+' COP';
  const certificado=(p,salario)=>({titulo:'Certificado laboral',lineas:[
    'Expedición: '+new Date().toLocaleDateString('es-CO'),p.nombre+' figura en este escenario ficticio como '+p.cargo+'.',
    'Ingreso del escenario: '+p.ingreso,...(salario?['Salario mensual simulado: '+money(p.salario)]:[]),
    'Documento de demostración. No acredita una relación laboral real.']});
  const nomina=(p,periodo,i)=>({titulo:'Comprobante de nómina',lineas:[p.nombre+' · '+p.cargo,'Período: '+periodo,
    'Salario base: '+money(p.salario),'Ajuste de ejemplo: '+money(i*50000),'Total devengado: '+money(p.salario+i*50000),
    'Deducción de ejemplo, salud: '+money(p.salario*.04),'Deducción de ejemplo, pensión: '+money(p.salario*.04),
    'Neto simulado: '+money(p.salario*.92+i*50000),'Conceptos y porcentajes ficticios pendientes de validación por Prebel.']});
  function pdf(d,id='DEMO') {
    const doc=new jspdf.jsPDF();doc.setProperties({title:d.titulo+' — demostración'});
    doc.setFillColor(36,65,94);doc.rect(0,0,210,44,'F');doc.setTextColor(255);doc.setFontSize(22);doc.text('prebel | Conecta',20,23);
    doc.setFontSize(10);doc.text('DEMOSTRACIÓN · DATOS FICTICIOS',20,34);doc.setTextColor(51,55,61);doc.setFontSize(19);doc.text(d.titulo,20,63);
    doc.setFontSize(10);doc.text('Referencia: '+id,20,74);doc.setFontSize(12);let y=89;
    for(const line of d.lineas){for(const row of doc.splitTextToSize(line,170)){if(y>260){doc.addPage();y=25;}doc.text(row,20,y);y+=7;}y+=4;}
    for(let i=1;i<=doc.getNumberOfPages();i++){doc.setPage(i);doc.setDrawColor(119,196,210);doc.line(20,277,190,277);doc.setFontSize(9);doc.text('SIN VALIDEZ LABORAL · Escenario ficticio para la hackatón',20,285);doc.text(String(i),185,285);}
    return doc;
  }
  return {certificado,nomina,pdf};
})();
