import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const root=path.dirname(fileURLToPath(import.meta.url));
const runtime='C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1111-570-0_26.1111.570.0_x64__3k8sg7r9htsxt/dependencies';
const {Presentation,PresentationFile}=await import(pathToFileURL(runtime+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs').href);
const e=JSON.parse(await fs.readFile(path.join(root,'VERIFICACION_DEFENSA.json'),'utf8'));
const timeline=JSON.parse(await fs.readFile(path.join(root,'TIEMPOS_DEFENSA.json'),'utf8'));
const p=Presentation.create({slideSize:{width:1280,height:720}});
const c={paper:'#F9FAF6', white:'#FFFFFF', ink:'#142B36', teal:'#00685E', green:'#DDEEE6', muted:'#435865', line:'#B9CAC6', accent:'#983A20'};
const script=[];
const font='Arial';
const synthetic=e.correctitude.results;
const by=(pattern,workers)=>synthetic.find(r=>r.pattern===pattern&&r.workers===workers);
const [base,projections,final]=['M101-BASE','M101-PROJ','M101-FINAL'].map(id=>e.montage[id]);
const count=(v)=>String(v).replace(/\B(?=(\d{3})+(?!\d))/g,'\u202F');
const n=(v,d=3)=>v.toFixed(d).replace('.',',');
const ratio=(r)=>n(r.required/r.observed,6);
const time=(t)=>n(t.duration_s,3);
const pct=(r)=>n(100*r.relative_savings,2)+' %';
const src={
  thesis:'Tesis, revisión 10. Capítulos 1, 3 y 4 y objetivos aprobados.',
  arch:'Configuración de las campañas de cinco patrones y M101 (generate_workflow.py y planes preservados). Manual de Pegasus, CondorIO y selección de sitios: https://pegasus.isi.edu/documentation/user-guide/running-workflows.html y https://pegasus.isi.edu/documentation/reference-guide/configuration.html. Manual de HTCondor, transferencia de archivos: https://htcondor.readthedocs.io/en/main/users-manual/file-transfer.html.',
  synthetic:'Validación cinco patrones del 10 de noviembre de 2026. VERIFICACION_REUNION.json, RESULTADOS_REUNION.csv y cápsulas nativas.',
  m101:'Tutorial oficial de Montage M101: https://irsa.ipac.caltech.edu/Montage/docs/m101tutorial.html. Experimento M101: PROTOCOLO.md y VERIFICACION_DEFENSA.json.',
  timing:'TIEMPOS_DEFENSA.json, reconstruido de jobstate.log en las cápsulas, y duración de las métricas DAGMan. Las marcas de eventos tienen resolución de un segundo.',
};

function shape(s,geometry,left,top,width,height,fill='none',stroke='none',weight=0){
  return s.shapes.add({geometry,position:{left,top,width,height},fill,line:{fill:stroke,width:weight}});
}
function text(s,value,x,y,w,h,size=28,fill=c.ink,bold=false,align='left'){
  const o=shape(s,'textbox',x,y,w,h);
  o.name=value.slice(0,55);
  o.text=value;
  o.text.style={typeface:font,fontSize:size,color:fill,bold,alignment:align,verticalAlignment:'middle',insets:0,autoFit:'none'};
}
function rule(s,x,y,w,fill=c.line){shape(s,'rect',x,y,w,1,fill);}
function arrow(s,x,y,w=52,fill=c.teal){shape(s,'rightArrow',x,y,w,18,fill);}
function node(s,label,x,y,w,h=80,active=false){
  shape(s,'rect',x,y,w,h,active?c.green:c.white,active?c.teal:c.line,1.5);
  text(s,label,x+8,y+5,w-16,h-10,25,c.ink,true,'center');
}
function slide(title,seconds,note,source,cover=false){
  const s=p.slides.add();s.background.fill=cover?c.ink:c.paper;
  if(!cover){
    text(s,title,72,42,1136,68,43,c.ink,true);
    rule(s,72,661,1136);
    text(s,seconds?'DME bajo CondorIO':'Respaldo',72,670,300,23,16,c.muted);
    text(s,String(p.slides.items.length).padStart(2,'0'),1145,670,63,23,16,c.muted,false,'right');
  }
  s.speakerNotes.text=note+'\n\nFuente: '+source;
  script.push({title,seconds,note,source});
  return s;
}
function table(s,values,widths,y,rowHeight=58,size=26){
  const tb=s.tables.add({rows:values.length,columns:widths.length,left:72,top:y,width:1136,height:values.length*rowHeight,columnWidths:widths,values});
  tb.styleOptions={headerRow:false,bandedRows:false,firstColumn:false};
  tb.borders.assign({style:'solid',fill:c.line,width:1});
  values.forEach((row,i)=>{
    tb.rows[i].height=rowHeight;
    row.forEach((_,j)=>{
      const cell=tb.getCell(i,j);
      cell.fill=i===0?c.ink:i%2===0?c.green:c.white;
      cell.text.style={typeface:font,fontSize:size,color:i===0?c.white:c.ink,bold:i===0||j===0,alignment:j===0?'left':'center',verticalAlignment:'middle'};
    });
  });
}
function highlight(s,label,y=570){text(s,label,72,y,1136,64,29,c.teal,true);}

let s=slide('Evaluación del movimiento de datos en flujos científicos',25,
  'Buenos días. Soy Luis Sebastián Contreras Díaz. En un flujo científico distribuido, una tarea puede estar lista para empezar y depender de archivos que están en otra máquina. Mi trabajo estudia cuánto movimiento exigen esas dependencias y qué entregas pueden reducirse.',src.thesis,true);
text(s,'TRABAJO DE GRADO',74,74,1110,35,22,'#9BD5CA',true);
text(s,'Evaluación del movimiento de\ndatos en flujos científicos',72,153,1136,184,62,c.white,true);
text(s,'Data Movement Efficiency (DME) en Pegasus bajo CondorIO',74,374,1130,59,32,'#C6E5DF');
rule(s,74,502,689,'#6E918E');
text(s,'Luis Sebastián Contreras Díaz',74,531,1130,42,29,c.white,true);
text(s,'Ingeniería de Sistemas y Computación\nUniversidad de los Andes',74,585,715,68,23,'#C6E5DF');

s=slide('Un flujo de trabajo también mueve datos',45,
  'Pensemos en un equipo que prepara observaciones, las procesa y reúne los resultados. Eso es un workflow, un conjunto de tareas conectadas por dependencias de datos. Una tarea necesita los archivos que otra produce. En flujos intensivos en datos, las tareas leen o generan archivos grandes o numerosos. Cuando las etapas corren en varias máquinas, esos archivos también se tienen que mover. Si se repite una entrega, puede repetirse un volumen considerable de datos.',src.thesis);
text(s,'Un workflow conecta tareas por los archivos que producen y consumen.',72,132,1136,57,30,c.teal,true);
node(s,'Preparar los datos',72,235,295,92);
arrow(s,387,271,64);
node(s,'Procesar los datos',472,235,322,92,true);
arrow(s,814,271,64);
node(s,'Reunir resultados',901,235,307,92);
text(s,'Entradas listas',330,342,177,46,22,c.muted,false,'center');
text(s,'Archivos intermedios',732,342,245,46,22,c.muted,false,'center');
rule(s,72,438,1136);
text(s,'Flujos intensivos en datos',72,466,1136,51,30,c.ink,true);
text(s,'Con archivos grandes o numerosos, una entrega repetida puede sumar muchos bytes.',72,532,1136,59,27,c.muted);

s=slide('¿Qué parte de los envíos era necesaria?',55,
  'A crea un archivo que B necesita. Incluso en la misma máquina, con jobs separados el archivo puede volver al coordinador, que es la máquina central, y salir otra vez hacia B. Si las tareas comparten un job, B puede leer la copia local. Un job es la unidad que se envía a ejecutar. Medir el total permite ver cuánto se movió. Para decidir dónde intervenir, también necesitamos saber qué parte exigía el flujo y qué entregas se pueden evitar conservando el resultado.',src.thesis);
text(s,'A crea un archivo que B necesita. Las dos tareas usan la misma máquina.',72,132,1136,50,29,c.teal,true);
text(s,'Jobs separados',72,230,214,72,25,c.ink,true);
node(s,'Tarea A',303,226,210);arrow(s,534,256,70);
node(s,'Coordinador',625,226,244);arrow(s,889,256,69);
node(s,'Tarea B',978,226,230);
text(s,'Retorno',506,188,132,31,19,c.muted,false,'center');
text(s,'Reenvío',856,188,130,31,19,c.muted,false,'center');
text(s,'Un job agrupado',72,388,214,72,25,c.ink,true);
shape(s,'rect',300,372,909,110,c.green,c.teal,1.5);
node(s,'Tarea A',326,386,210);arrow(s,564,417,328);
node(s,'Tarea B',924,386,255);
text(s,'En un mismo job, B puede leer la copia local.',72,526,1136,50,28,c.ink);
highlight(s,'Analizar los envíos permite localizar dónde se puede ahorrar.',574);

s=slide('Arquitectura de ejecución y staging',75,
  'El coordinador ejecuta Pegasus y DAGMan. Pegasus convierte las tareas y dependencias en un plan de jobs. RoundRobin es el selector de sitios de Pegasus. Alterna entre sitios elegibles cuando hay varios. Aquí usamos un único sitio de ejecución, el pool de HTCondor. DAGMan envía un job cuando se cumplen sus dependencias y HTCondor le asigna un worker compatible y disponible. En las pruebas de patrones recuperamos esa asignación del historial. En Montage fijamos la máquina de cada tarea para comparar las agrupaciones. CondorIO define el staging, es decir, cómo se preparan las entradas y se devuelven las salidas. El coordinador y los workers tienen discos locales separados. HTCondor copia las entradas al directorio aislado de cada job y devuelve al coordinador las salidas declaradas. Así, un intermedio que necesita otro worker pasa por el coordinador.',src.arch);
text(s,'Planificación y ejecución',72,116,1136,34,24,c.teal,true);
node(s,'Pegasus\nPrepara el plan',72,159,300,87);
arrow(s,390,194,65);
node(s,'DAGMan\nEnvía los jobs listos',473,159,332,87);
arrow(s,823,194,65);
node(s,'HTCondor\nAsigna el worker',906,159,302,87,true);
text(s,'RoundRobin selecciona sitios. Usamos un único sitio de ejecución.',72,263,1136,47,26,c.ink);
rule(s,72,327,1136);
text(s,'Staging con CondorIO',72,344,1136,43,30,c.teal,true);
node(s,'Coordinador',72,421,291,115,true);
node(s,'Worker\nDirectorio del job',918,421,290,115,true);
text(s,'Entradas al directorio del job',380,402,522,33,22,c.muted,false,'center');
arrow(s,394,435,494);
shape(s,'leftArrow',394,497,494,18,c.teal);
text(s,'Salidas declaradas al coordinador',380,515,522,34,22,c.muted,false,'center');
text(s,'Discos locales separados. Los archivos entre workers pasan por el coordinador.',72,579,1136,52,25,c.ink,true);

s=slide('DME mide qué parte del volumen era necesaria',60,
  'Mi objetivo fue definir una métrica para evaluar ese movimiento, automatizar el cálculo y validarlo. La métrica se llama DME, eficiencia del movimiento de datos. Pongo en el numerador los bytes requeridos por las dependencias y por la ubicación real de las tareas. En el denominador sumo los bytes de cada entrega completa que pude corroborar. Calculo la razón cuando el observado es positivo y puedo corroborar todas las entregas requeridas. El cociente indica qué fracción del volumen observado era requerida. Uno indica que los volúmenes coinciden. Un medio indica que la mitad del observado supera lo requerido. El desglose conserva el archivo y su destino, así que también permite ubicar el exceso.',src.thesis);
text(s,'DME  =',80,178,330,163,74,c.teal,true);
text(s,'Volumen requerido',431,177,725,71,46,c.ink,true,'center');
rule(s,433,260,721,c.teal);
text(s,'Volumen observado',431,276,725,70,46,c.ink,true,'center');
text(s,'Requerido',73,392,278,50,28,c.ink,true);
text(s,'Una cuenta por archivo y destino que necesita recibirlo.',360,392,848,50,27,c.muted);
text(s,'Observado',73,470,278,50,28,c.ink,true);
text(s,'Una cuenta por cada entrega completa corroborada.',360,470,848,50,27,c.muted);
highlight(s,'DME = 1 si se cumplen las obligaciones y los volúmenes coinciden.');

s=slide('Por qué cuenta el destino de cada archivo',45,
  'Dos tareas leen el mismo archivo que sale del coordinador. En una máquina basta una copia. Si están en máquinas distintas, hace falta una copia por destino. Si observo dos entregas en ambos casos, DME es un medio en el primero y uno en el segundo. Por eso el requerido cuenta destinos y usa la ubicación real. También cuenta el relevo por el coordinador cuando CondorIO lo exige. Si el requerido se mantiene, reducir el observado aumenta DME.',src.thesis+' Ejemplo ilustrativo de una entrada compartida.');
text(s,'Ejemplo con un archivo compartido y dos entregas registradas.',72,127,1136,50,29,c.muted);
const scenarios=[
  ['Las dos tareas en una máquina','1 copia requerida','DME = 1/2'],
  ['Una tarea en cada máquina','2 copias requeridas','DME = 1']
];
for(const [i,[label,required,dme]] of scenarios.entries()){
  const x=72+i*588;
  text(s,label,x,219,550,54,28,c.ink,true);
  if(i===0){
    shape(s,'rect',x,301,520,91,c.green,c.teal,1.5);
    node(s,'Tarea A',x+16,312,226,69);
    node(s,'Tarea B',x+278,312,226,69);
  }else{
    node(s,'Tarea A',x,309,245,75,true);
    node(s,'Tarea B',x+275,309,245,75,true);
  }
  text(s,required,x,412,520,44,27,c.muted);
  text(s,dme,x,471,520,67,40,c.teal,true);
}
rule(s,72,559,1136);
text(s,'El número de copias necesarias cambia con la ubicación de las tareas.',72,578,1136,49,27,c.ink);

s=slide('Plan de pruebas',60,
  'Dividí la evaluación en dos preguntas. Primero, ¿la herramienta obtiene los volúmenes correctos? Usé cinco formas de conectar tareas, con dos o cuatro máquinas de trabajo disponibles y un núcleo por máquina. Mantuve seis tareas por flujo, archivos de diez MiB, el trabajo de CPU y las reglas de retorno. Segundo, ¿DME refleja un ahorro al cambiar la ejecución de un flujo real? Usé un mosaico completo de Montage. Corrí una base con tareas separadas y dos variantes que reúnen pares distintos. Conservé las entradas, el grafo y las máquinas. Eso permite atribuir el cambio de bytes a los envíos que elimina cada agrupación.',src.synthetic+' '+src.m101);
text(s,'1. ¿El cálculo da el valor esperado?',72,153,1136,56,32,c.teal,true);
text(s,'Cinco patrones, con dos y cuatro máquinas disponibles.\nComparamos la cuenta independiente con el resultado de Analyzer.',72,226,1136,88,28,c.ink);
rule(s,72,353,1136);
text(s,'2. ¿DME refleja el ahorro al agrupar tareas?',72,398,1136,56,32,c.teal,true);
text(s,'Un mosaico de Montage, una base y dos agrupaciones.\nComparamos los bytes observados y DME con el mismo requerido.',72,469,1136,91,28,c.ink);

const d2=by('Distribución',2),d4=by('Distribución',4);
s=slide('Requerido y observado en distribución',85,
  'Analyzer lee el plan de Pegasus y el historial de HTCondor. Reconstruye los destinos de los archivos y las entregas completas. Para comprobarlo hice una cuenta independiente. En distribución un productor recibe A, genera g y cinco tareas leen g. Cada archivo pesa diez MiB. A entra una vez y los cinco resultados vuelven una vez cada uno. Ahí coinciden requerido y observado. Con dos workers, dos consumidores de g quedaron en W2. Con cuatro, uno quedó en W4. En ambas corridas hay un solo worker consumidor distinto del que produjo g. Por eso el requerido de g son dos tramos: el retorno al coordinador y una entrega a esa máquina. En los registros vimos un retorno y cinco entregas de g, una por job consumidor. Así, el requerido suma ochenta MiB y el observado ciento veinte. Analyzer obtuvo la misma cuenta. El cociente dos tercios dice que dos tercios de lo entregado correspondían a obligaciones del flujo.',src.synthetic);
text(s,'Un productor crea g. Cinco tareas lo leen. Cada archivo pesa 10 MiB.',72,123,1136,52,28,c.teal,true);
node(s,'Entrada A',72,186,220,62);
arrow(s,309,207,51);
node(s,'Productor',376,186,223,62);
arrow(s,622,207,79);
text(s,'g',630,174,65,27,21,c.muted,true,'center');
node(s,'5 consumidores',724,186,484,62,true);
table(s,[['Archivo','Requerido (MiB)','Observado (MiB)'],
  ['Entrada A','10 · una entrada','10 · una entrega'],
  ['Intermedio g','20 · retorno y un destino remoto','60 · retorno y cinco envíos'],
  ['Cinco finales','50 · cinco archivos al coordinador','50 · cinco entregas'],
  ['Total',String(d2.required_mib),String(d2.observed_mib)]
],[236,450,450],277,54,23);
highlight(s,'Con 2 y 4 workers, DME = '+d2.required_mib+' / '+d2.observed_mib+' = '+d2.dme+'.',548);
text(s,'Dos tercios del observado cubren obligaciones. El exceso suma 40 MiB.',72,608,1136,38,23,c.muted);

const a2=by('Agregación',2),a4=by('Agregación',4);
s=slide('El cálculo coincidió en los cinco patrones',60,
  'Estas son las cinco estructuras que probamos. La cuenta independiente y Analyzer coincidieron en los dos volúmenes y en DME en las diez ejecuciones. Ya vimos por qué distribución dio dos tercios en ambos ambientes. En agregación y redistribución sí cambió el requerido. En cada uno, quedó un productor adicional en una máquina distinta de su consumidor. Su archivo añadió dos tramos obligatorios, de vuelta al coordinador y del coordinador al consumidor. Eso agregó veinte MiB requeridos, con el mismo observado en cada patrón. Por eso leemos DME junto con sus dos volúmenes.',src.synthetic);
const patternDescription=['Tareas independientes','Una tarea tras otra','Varios archivos se reúnen','Varias tareas leen un archivo','Se reúne y se reparte'];
const syntheticRows=synthetic.filter(row=>row.workers===2);
table(s,[['Patrón','Cómo se conectan las tareas','DME con 2','DME con 4'],
  ...syntheticRows.map((row,i)=>[row.pattern,patternDescription[i],row.dme,by(row.pattern,4).dme])
],[260,510,183,183],143,56,23);
highlight(s,'En agregación, ambos casos movieron '+a2.observed_mib+' MiB con distinto requerido.',530);
text(s,'DME con 2 o 4 máquinas disponibles. Coincidencia en las 10 ejecuciones.',72,592,1136,39,21,c.muted);

const wait2=e.timing['AGGREGATION-W2'].first_submit_to_execute_s;
const wait4=e.timing['AGGREGATION-W4'].first_submit_to_execute_s;
const dist2=timeline['DISTRIBUTION-W2'],dist4=timeline['DISTRIBUTION-W4'];
const firstConsumers=(row)=>Math.min(...Object.entries(row.jobs.SUBMIT).filter(([task])=>!task.endsWith('_T1')).map(([,second])=>second));
const distSubmit2=firstConsumers(dist2),distSubmit4=firstConsumers(dist4);
s=slide('Mismos bytes, distintos tiempos',55,
  'Distribución movió ciento veinte MiB en ambas corridas. Con cuatro workers, DAGMan envió los consumidores cinco segundos antes y terminó cerca de cinco segundos antes. Los registros muestran dónde aparece la diferencia. En agregación pasó al revés. El primer job tardó dieciséis segundos en empezar tras el envío, frente a seis con dos workers. Con una ejecución por ambiente, describimos lo que pasó en esas corridas. Para atribuir esas esperas a una causa específica necesitaríamos repetir bajo condiciones controladas.',src.timing);
text(s,'Distribución movió '+d2.observed_mib+' MiB con dos y con cuatro workers.',72,123,1136,53,29,c.teal,true);
table(s,[['Momento desde el inicio del flujo','2 workers','4 workers'],
  ['Envío de los cinco consumidores',distSubmit2+' s',distSubmit4+' s'],
  ['Fin del último consumidor',dist2.last_terminated_s+' s',dist4.last_terminated_s+' s'],
  ['Duración completa',time(d2)+' s',time(d4)+' s']
],[590,273,273],200,69,26);
text(s,'El productor debe terminar antes de que se envíen los consumidores.',72,504,1136,50,28,c.ink,true);
text(s,'Una corrida por ambiente. Los eventos ubican la diferencia de tiempo.',72,569,1136,46,23,c.muted);

s=slide('Un flujo real de astronomía con Montage',35,
  'Con el cálculo comprobado, pasé a un flujo real. Montage toma imágenes astronómicas que cubren partes del cielo y las combina en un mosaico. Este es M101. Usé la ruta del tutorial sin ajuste de fondo y partí de diez imágenes 2MASS. La salida científica son dos archivos FITS: el mosaico y un mapa que indica qué área queda cubierta. La comparación pregunta si podemos producir esos mismos resultados haciendo menos entregas entre jobs.',src.m101+' Vista del FITS de la ejecución base con mViewer.');
const mosaicImage=await fs.readFile(path.join(root,'m101_preview_slides.png'));
s.images.add({blob:mosaicImage.buffer.slice(mosaicImage.byteOffset,mosaicImage.byteOffset+mosaicImage.byteLength),
              contentType:'image/png',alt:'Mosaico M101 producido en la ejecución base, renderizado en escala de grises',
              fit:'contain',position:{left:729,top:136,width:479,height:466}});
text(s,'Mosaico M101 obtenido en la ejecución base',729,606,479,34,20,c.muted,false,'center');
text(s,'Diez imágenes del cielo entran.\nUn mosaico y su mapa de\ncobertura salen.',72,170,615,167,34,c.ink,true);
rule(s,72,365,607);
text(s,'¿Podemos obtener los mismos\nresultados moviendo menos datos?',72,424,620,112,30,c.teal,true);

s=slide('El workflow completo de M101',70,
  'A la izquierda están las diez tareas de reproyección, P01 a P10. Cada una toma su propia imagen y una cabecera común que define las coordenadas de destino. Cada tarea produce una imagen alineada y su mapa de área. Todas las reproyecciones corren en W2. En W1, mImgtbl recibe las diez imágenes alineadas y genera una tabla con su información. mAdd recibe esa tabla, las imágenes y sus áreas, y la cabecera. Con eso escribe el mosaico y su mapa de cobertura. Las flechas muestran dependencias. Los envíos entre máquinas pasan por el coordinador. En la base cada caja de tarea es un job, doce en total. La ubicación y las dependencias se mantienen cuando agrupamos.',src.m101);
text(s,'Las flechas indican qué archivos necesita cada tarea.',72,109,1136,34,23,c.muted);
shape(s,'rect',72,151,465,394,c.white,c.line,1.5);
shape(s,'rect',779,151,429,394,c.white,c.line,1.5);
text(s,'W2  ·  Reproyectar imágenes',93,166,428,49,26,c.teal,true);
text(s,'W1  ·  Construir el mosaico',800,166,392,49,26,c.teal,true);
text(s,'10 tareas mProject',93,215,428,35,22,c.muted);
for(let i=0;i<10;i++){
  const x=93+(i%5)*83;
  const y=262+Math.floor(i/5)*70;
  node(s,'P'+String(i+1).padStart(2,'0'),x,y,72,54,true);
}
text(s,'Cada tarea lee una imagen original\ny la cabecera común.',93,428,415,76,23,c.muted);
node(s,'Crear tabla · mImgtbl',801,248,385,66,true);
node(s,'Combinar · mAdd',801,407,385,66,true);
arrow(s,547,274,221);
arrow(s,547,432,221);
text(s,'10 imágenes\nalineadas',545,218,221,48,21,c.muted,false,'center');
text(s,'10 imágenes\ny sus áreas',545,375,221,48,21,c.muted,false,'center');
shape(s,'downArrow',977,323,22,74,c.teal);
text(s,'Tabla de imágenes',1010,331,173,48,19,c.muted);
text(s,'mAdd lee también la cabecera común.',801,485,382,39,20,c.muted);
text(s,'12 tareas, 12 jobs en la base',72,563,393,60,25,c.ink,true);
text(s,'Salida del flujo · Mosaico FITS y mapa de cobertura',466,563,742,60,26,c.teal,true);

const frameSavings=final.avoided.filter(row=>/^p\d\d\.fits$/.test(row[0])).reduce((total,row)=>total+row[4]*row[5],0);
const tableSavings=final.savings-frameSavings;
s=slide('Dónde cambiamos el workflow',75,
  'Probé dos tipos de agrupación de pares sin mover las tareas de máquina. En W2, P01 y P02 comparten la cabecera, de '+count(projections.savings)+' bytes. Cada tarea sigue leyendo su propia imagen. Al revisar el grafo vemos que los otros pares de reproyección comparten esa misma cabecera. En W1 hay un solo par: la tabla y la combinación. Con jobs separados, las diez imágenes alineadas llegan a ambos jobs. Al reunir las tareas, llegan una vez y la tabla se lee dentro del mismo job. Los dos cambios quitan un job. El ahorro depende de cuánto pesan las entregas que desaparecen.',src.m101+' Análisis por pares de la especificación M101-BASE con ubicación fija.');
text(s,'Variante 1 · P01 y P02 comparten un job en W2',72,136,1136,43,29,c.ink,true);
node(s,'Cabecera común',72,200,285,74);
arrow(s,380,228,62);
shape(s,'rect',465,194,413,86,c.green,c.teal,1.5);
node(s,'P01',488,207,151,59);
node(s,'P02',704,207,151,59);
text(s,'Una entrega evitada\n'+count(projections.savings)+' bytes',908,190,300,94,26,c.teal,true);
rule(s,72,326,1136);
text(s,'Variante 2 · mImgtbl y mAdd comparten un job en W1',72,354,1136,43,29,c.ink,true);
node(s,'10 imágenes alineadas',72,417,285,74);
arrow(s,380,445,62);
shape(s,'rect',465,411,413,86,c.green,c.teal,1.5);
node(s,'mImgtbl',481,424,157,59);
arrow(s,648,444,45);
node(s,'mAdd',704,424,157,59);
text(s,'Once entregas evitadas\n'+count(final.savings)+' bytes',908,407,300,94,25,c.teal,true);
highlight(s,'Las diez imágenes entran una vez. La tabla se lee en el mismo job.',550);

s=slide('La mejor agrupación ahorró '+pct(final),85,
  'El requerido fue el mismo porque las tareas conservaron los archivos y su ubicación. Al juntar la tabla y la combinación evitamos más de cuarenta y dos millones de bytes. El observado bajó un '+pct(final)+' y DME pasó de '+ratio(base)+' a '+ratio(final)+'. Los píxeles y la geometría del mosaico y del mapa coincidieron. La agrupación final también terminó antes en esta corrida. El primer job ya había empezado dieciocho segundos antes que en la base, cuando todavía faltaba ejecutar la agrupación final. La duración, por tanto, recoge diferencias que aparecen en varias etapas. Para escoger por volumen, la opción que medimos con menos bytes fue agrupar la tabla y la combinación.',src.m101+' '+src.timing);
text(s,'Requerido común: '+count(base.required)+' bytes',72,125,1136,54,30,c.muted);
table(s,[['Configuración','Jobs','Observado (bytes)','DME','Duración (s)'],
  ['Base sin agrupación',String(base.jobs),count(base.observed),ratio(base),n(base.duration)],
  ['Dos reproyecciones juntas',String(projections.jobs),count(projections.observed),ratio(projections),n(projections.duration)],
  ['Tabla y combinación juntas',String(final.jobs),count(final.observed),ratio(final),n(final.duration)]
],[397,95,287,174,183],194,66,24);
highlight(s,'Ahorro frente a la base: '+count(final.savings)+' bytes ('+pct(final)+').',482);
text(s,'Mismo mosaico y mapa de cobertura. Una corrida por configuración.',72,552,1136,53,26,c.muted);

s=slide('Conclusiones',40,
  'La cuenta independiente coincidió con Analyzer en los cinco patrones y los dos ambientes. En el mosaico completo, DME mejoró cuando la agrupación evitó entregar de nuevo imágenes que dos tareas podían compartir. La diferencia se explica por los archivos que dejaron de moverse. Mi conclusión es que DME permite medir la cercanía al requerido de una ejecución y explicar el exceso por archivo y destino. Para elegir una configuración por volumen miro el observado, y para elegirla por tiempo necesito medir duración en condiciones comparables. La evidencia corresponde a CondorIO y a los grafos y configuraciones probados. Gracias.',src.thesis+' '+src.synthetic+' '+src.m101);
for(const [i,[head,body]] of [
  ['Correctitud','La cuenta independiente coincidió en los cinco patrones.'],
  ['Sensibilidad','En M101, compartir las imágenes redujo el observado y elevó DME.'],
  ['Decisión','Los bytes observados permiten elegir por volumen. DME explica la diferencia.'],
].entries()){
  const y=166+i*133;
  text(s,head,72,y,264,58,30,c.teal,true);
  text(s,body,336,y,872,70,29,c.ink);
  rule(s,72,y+91,1136);
}
text(s,'Alcance: CondorIO, grafos y configuraciones evaluados.',72,579,1136,48,25,c.muted);

s=slide('Resultados de los cinco patrones',0,
  'Respaldo. Todas las razones usan los valores de las columnas requerido y observado. Cada celda corresponde a una ejecución. El observado por patrón quedó constante entre ambientes. La ubicación cambió el requerido en agregación y redistribución. En este último patrón, ambos productores quedaron en W1/W2 y W3/W4 respectivamente. El agregador y las etapas posteriores quedaron en W1 y W2 respectivamente. Así se pasó de un archivo productor remoto a dos. Los demás archivos conservaron el mismo número de destinos requeridos.',src.synthetic);
table(s,[['Patrón','2W req./obs.','2W DME','2W s','4W req./obs.','4W DME','4W s'],
  ...synthetic.filter(r=>r.workers===2).map(r=>{const a=by(r.pattern,4);return [r.pattern,r.required_mib+' / '+r.observed_mib,r.dme,time(r),a.required_mib+' / '+a.observed_mib,a.dme,time(a)];})
],[232,191,119,133,191,119,151],151,64,21);
text(s,'Volúmenes en MiB. Duración del DAG en segundos.',72,555,1136,52,25,c.muted);

s=slide('Duración con dos y cuatro workers',0,
  'En agregación, los cinco productores pueden avanzar antes del agregador. Con cuatro máquinas arrancaron cuatro productores casi juntos. En los registros pasaron '+wait4+' segundos desde el envío hasta el evento de inicio del primer job con cuatro máquinas, frente a '+wait2+' con dos. La fase paralela comenzó más tarde y la ejecución completa duró cerca de cuatro segundos más. Con una corrida por ambiente se puede localizar el intervalo donde aparece la diferencia. Para atribuir esa espera a una causa concreta harían falta más ejecuciones y control de carga y planificación. En procesamiento, las seis tareas son independientes y la ejecución con cuatro terminó antes.',src.timing);
table(s,[['Agregación','2 workers','4 workers'],['Del envío al inicio del primer job',wait2+' s',wait4+' s'],['Duración del flujo',time(a2)+' s',time(a4)+' s']],[580,278,278],162,83,27);
text(s,'El agregador espera a sus cinco productores.',72,450,1136,58,32,c.teal,true);
text(s,'Una ejecución por ambiente. Los intervalos describen estas corridas.',72,526,1136,52,26,c.muted);

s=slide('Qué entregas elimina cada agrupación',0,
  'Respaldo. Para calcular el ahorro resté el multiconjunto de entregas de cada variante al de la base. Cada entrega se identifica por archivo, dirección, origen, destino y tamaño. La auditoría concilia los bytes y conteos nativos de las direcciones científicas, separando sus archivos auxiliares. Este desglose ubica el mecanismo de ahorro.',src.m101);
table(s,[['Agrupación','Movimiento que desaparece','Bytes'],
  ['Dos reproyecciones','Una entrega de template.hdr',count(projections.savings)],
  ['Tabla y coadición','Diez entregas de imágenes reproyectadas',count(frameSavings)],
  ['Tabla y coadición','Movimiento de images.tbl',count(tableSavings)],
  ['Tabla y coadición','Ahorro total frente a la base',count(final.savings)]
],[317,599,220],147,70,24);
highlight(s,'El ahorro se reconstruye con los contratos y el historial de HTCondor.',535);

s=slide('Alcance de las afirmaciones',0,
  'Respaldo. Si cambia el requerido, DME compara proximidad a la cota de cada ubicación. La clasificación por bytes se obtiene con el observado. La cota es inferior bajo cobertura, y su alcanzabilidad depende de la configuración y de las reglas de transferencia. En M101 comparamos solo dos agrupaciones frente a la base. Para afirmar una mejora de tiempo habría que medir repetidamente y contrastar los intervalos del DAG. El objetivo de validación conserva como pendiente aislar el costo de captura nativa. El dato nuevo de M101 es la sensibilidad de DME, no una medición de ese costo.',src.thesis+' '+src.m101);
for(const [i,[head,body]] of [
  ['Mejor agrupación','La de menor observado entre las configuraciones comparadas.'],
  ['Cobertura','Cada obligación tiene su propia entrega corroborada.'],
  ['Duración','Se interpreta con el grafo y los eventos de ejecución.'],
  ['Instrumentación','Queda por aislar el costo de captura nativa.'],
].entries()){
  const y=145+i*111;
  text(s,head,72,y,310,65,27,c.teal,true);
  text(s,body,389,y,818,65,26,c.ink);
  rule(s,72,y+83,1136);
}

const clock=(seconds)=>String(Math.floor(seconds/60)).padStart(2,'0')+':'+String(seconds%60).padStart(2,'0');
let elapsed=0;
const guion=['# Guion de defensa de DME','','Quince diapositivas principales. Duración objetivo **14:30**, con 30 segundos de margen. Cuatro diapositivas de respaldo para preguntas.',''];
for(const [i,entry] of script.entries()){
  const interval=entry.seconds?clock(elapsed)+'–'+clock(elapsed+entry.seconds):'Respaldo';
  guion.push('## '+(i+1)+'. '+entry.title,'','**'+interval+'**','',entry.note,'');
  elapsed+=entry.seconds;
}
guion.push('## Preguntas del jurado','',
  '**¿Qué hace RoundRobin en el experimento?** Es el selector de sitios de Pegasus. El plan usa un único sitio de ejecución, `condorpool`. HTCondor asigna los jobs a los workers compatibles según las restricciones y los recursos disponibles. Para el cálculo usamos la máquina que quedó en el historial. En Montage fijamos la ubicación para aislar el efecto de agrupar.','',
  '**¿Qué significa staging con CondorIO?** Preparar los archivos que necesita un job y recoger sus salidas declaradas. HTCondor copia las entradas del coordinador al directorio aislado del job y devuelve las salidas declaradas. Si otro worker necesita un intermedio, el coordinador lo entrega de nuevo al job receptor.','',
  '**¿Cuál agrupación optimiza más?** Entre las dos ensayadas, tabla y coadición. Ambas ahorran un job. La agrupación de dos reproyecciones evita una entrega de la cabecera. La agrupación final evita entregar de nuevo las diez imágenes reproyectadas y mover la tabla. La comparación se limita al mismo grafo, ubicación y política de transferencia.','',
  '**¿Hace falta un Montage más complejo?** M101 basta para explicar este mecanismo. El grafo completo tiene doce tareas y conserva los dos FITS finales. Si agrupo exactamente dos tareas sin cambiarlas de máquina, hay 45 pares posibles de reproyecciones en W2 y un par en W1. Los 45 comparten únicamente la cabecera de 318 bytes. El par de W1 comparte diez imágenes y consume la tabla que él mismo produce. Eso se deduce del grafo y del contrato de archivos. Medí una configuración de cada tipo. El análisis queda acotado a agrupar dos tareas con ubicación fija.','',
  '**¿Por qué distribución dio lo mismo con dos y cuatro workers?** Con dos workers, el productor quedó en W1 y dos consumidores en W2. Con cuatro workers, el productor quedó en W3 y un consumidor en W4. En cada caso hay una sola máquina remota que necesita g. El requerido son 10 MiB de entrada, 20 del intermedio y 50 de finales. El observado son 10, 60 y 50 MiB, respectivamente, porque se corroboraron cinco entregas de g a jobs separados y un retorno. DME es 80/120 en los dos casos.','',
  '**¿Por qué se llama mosaico completo?** Parte de las diez entradas FITS y llega a un mosaico FITS y su mapa de cobertura. Se usa la ruta oficial sin ajuste de fondo. Las tres ejecuciones recorren las mismas doce tareas científicas.','',
  '**¿Por qué se ven franjas en la portada?** La ruta del tutorial combina las imágenes sin igualar previamente sus fondos. Esa elección se mantuvo en las tres configuraciones. La portada muestra la imagen medida con un ajuste de contraste para visualización.','',
  '**¿Por qué DME subió en agregación con cuatro workers si el observado siguió igual?** Un productor adicional quedó lejos del agregador y su intermedio añadió dos entregas obligatorias. Cambió el requerido. Los bytes observados empataron.','',
  '**¿Por qué dos workers fueron más rápidos en algunos casos?** En agregación, los registros muestran '+wait2+' y '+wait4+' segundos desde el envío de los productores hasta la primera ejecución. La fase paralela comenzó más tarde con cuatro workers. Con una corrida por ambiente, esa localización del retraso queda respaldada y su causa específica queda abierta.','',
  '**¿Se mantuvo la salida científica?** Sí. El mosaico y su mapa de cobertura coincidieron en los datos binarios de píxeles y en las tarjetas FITS comparadas, incluidas las de geometría.','',
  '**¿Por qué DME queda cerca de uno?** En la agrupación final quedan '+count(final.observed-final.required)+' bytes de exceso. Son nueve entregas adicionales de la cabecera a W2, de 318 bytes cada una, más el retorno de la tabla al coordinador, de 6 284 bytes.','',
  '**¿Por qué una ejecución por variante?** El objetivo del contraste es cotejar una cuenta de bytes determinada por el grafo, los tamaños, la colocación y las entregas. La auditoría corrobora cada entrega. La duración se reporta como descripción de cada corrida.','',
  '**¿El requerido es siempre alcanzable?** La cobertura garantiza que es una cota inferior. Alcanzarla depende de las restricciones de los jobs y del mecanismo de transferencia. La tesis incluye un contraejemplo para un grafo concreto con jobs aislados y sin caché.','',
  '**¿Qué queda pendiente en los objetivos?** Se caracterizaron los patrones, se definió DME, se implementó el cálculo y se evaluaron la correctitud y la sensibilidad. La validación conserva un componente parcial, el costo de captura nativa.','',
  '**Si quedan dos minutos al empezar Montage:** muestra el grafo, señala tabla y coadición y explica qué entregas se eliminan. Cierra con el alcance de la comparación y el criterio para elegir por volumen.','',
  '## Cómo explicar cada resultado y su tiempo','',
  'Las marcas de eventos son segundos desde el inicio del flujo. La duración de DAGMan tiene mayor precisión. Cada comparación describe las corridas disponibles.','',
  '- **Procesamiento.** Las seis tareas tienen archivos propios. En ambos ambientes se requieren y se observan 120 MiB, seis entradas y seis finales. DME vale uno. Con cuatro workers comenzaron cuatro jobs a la vez, y con dos comenzaron dos. El intervalo entre el inicio del primero y el fin del último bajó de 14 a 9 s. El flujo completo pasó de 101,949 a 90,984 s.','',
  '- **Pipeline.** Las seis tareas en cadena quedaron en una sola máquina en ambos casos. La entrada y el final suman 20 MiB requeridos. Los cinco intermedios añaden un retorno y un reenvío por archivo, para 120 MiB observados. La ventana de los jobs científicos fue de 103 y 102 s. Tras el último job transcurrieron 26 y 22 s hasta el cierre. El flujo completo pasó de 181,368 a 176,423 s.','',
  '- **Agregación.** Cinco productores entregan sus intermedios a un agregador. Con cuatro workers, un productor adicional quedó fuera de la máquina del agregador y su archivo agregó 20 MiB requeridos. El observado se mantuvo en 160 MiB. La espera tras el primer envío pasó de 6 a 16 s y la ventana de jobs científicos pasó de 32 a 28 s. El flujo completo pasó de 106,254 a 110,199 s.','',
  '- **Distribución.** El único destino remoto de g explica por qué se conservaron 80 MiB requeridos, 120 MiB observados y DME de dos tercios. Con cuatro workers el productor terminó a los 62 s frente a 66 s con dos. DAGMan envió los consumidores a los 76 s frente a 81 s. El flujo pasó de 136,178 a 131,380 s.','',
  '- **Redistribución.** Con dos workers un productor estaba fuera de la máquina del agregador. Con cuatro estaban fuera los dos. El requerido pasó de 60 a 80 MiB y el observado quedó en 140 MiB. El primer job empezó 10 s después del envío con dos workers y 23 s después con cuatro. El flujo completo pasó de 151,274 a 161,405 s.','',
  '- **Montage.** La base duró 251,237 s. La agrupación de dos reproyecciones duró 256,224 s y su ventana de jobs científicos fue más larga, 170 frente a 156 s. La agrupación de tabla y combinación duró 222,195 s. Su primer job empezó 18 s antes que el de la base y su ventana de jobs científicos duró 10 s menos. La diferencia de duración ya se estaba acumulando antes de la agrupación final. El ahorro de bytes se atribuye a las entregas eliminadas. Para aislar su efecto temporal harían falta más ejecuciones.','',
  '## Evidencia','',
  '- Manual de Pegasus sobre [CondorIO](https://pegasus.isi.edu/documentation/user-guide/running-workflows.html) y [selección de sitios](https://pegasus.isi.edu/documentation/reference-guide/configuration.html).',
  '- [Manual de HTCondor sobre transferencia de archivos](https://htcondor.readthedocs.io/en/main/users-manual/file-transfer.html).',
  '- [Tutorial oficial de Montage](https://irsa.ipac.caltech.edu/Montage/docs/m101tutorial.html).','- Validación de cinco patrones, 10 de noviembre de 2026. RESULTADOS_REUNION.csv y jobstate.log de las cápsulas.','- Experimento M101, 11 de noviembre de 2026. VERIFICACION_DEFENSA.json, auditorías independientes y FITS_EQUIVALENCE.json.','');

await fs.writeFile(path.join(root,'guion_arquitectura.md'),guion.join('\n'),'utf8');
await (await PresentationFile.exportPptx(p)).save(path.join(root,'candidato_arquitectura.pptx'));
console.log(JSON.stringify({slides:p.slides.items.length,seconds:elapsed}));
