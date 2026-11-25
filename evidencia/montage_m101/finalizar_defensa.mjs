import fs from 'node:fs/promises';
import {constants} from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const build=path.dirname(fileURLToPath(import.meta.url));
const workspace=path.dirname(build);
const runtime='C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1111-570-0_26.1111.570.0_x64__3k8sg7r9htsxt/dependencies';
const skill='C:/Users/Acer/.codex/plugins/cache/openai-primary-runtime/presentations/26.1111.10930/skills/presentations/container_tools';
process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';
const {finalizePresentation}=await import(pathToFileURL(skill+'/artifact_tool_utils.mjs').href);
const {FileBlob,PresentationFile}=await import(pathToFileURL(runtime+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs').href);
const candidatePath=path.join(build,'candidato_arquitectura.pptx');
const output=path.join(workspace,'output/presentacion');
const finalPath=path.join(output,'Presentacion_Defensa_DME_M101_Arquitectura.pptx');
const tableOwners=[8,9,10,14,16,17,18];
const result=await finalizePresentation({
  workspaceDir:workspace,candidatePath,finalPath,
  pythonExecutable:runtime+'/python/python.exe',
  integrityValidatorPath:skill+'/inspect_presentation_package_integrity.py',
  layoutValidatorPath:skill+'/inspect_presentation_layout_geometry.py',
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',
              ...tableOwners.flatMap(n=>['--require-native-table-slide',String(n)])],
  explicitTotalSlideCount:19,
  requiredNativeTableOwnerSlides:tableOwners,
  fontPolicy:{basis:'design',families:['Arial']},
  verifyArtifactToolImport:true,
  receiptPath:path.join(build,'PPTX_VALIDACION_ARQUITECTURA.json'),
}).catch(async error=>{
  if(error.code!=='EPERM'||error.syscall!=='link'||error.dest!==finalPath||!error.path.endsWith('.validated')) throw error;
  await fs.copyFile(candidatePath,finalPath,constants.COPYFILE_EXCL);
  if(!(await fs.readFile(candidatePath)).equals(await fs.readFile(finalPath))) throw new Error('Los archivos difieren');
  return {finalPath,publication:'validated candidate copied byte for byte'};
});
const deck=await PresentationFile.importPptx(await FileBlob.load(finalPath));
const renders=path.join(build,'render_arquitectura');
await fs.mkdir(renders,{recursive:true});
for(const [i,s] of deck.slides.items.entries()){
  const png=await deck.export({slide:s,format:'png',scale:1});
  await fs.writeFile(path.join(renders,String(i+1).padStart(2,'0')+'.png'),new Uint8Array(await png.arrayBuffer()));
}
await fs.copyFile(path.join(build,'guion_arquitectura.md'),path.join(output,'Guion_Defensa_DME_M101_Arquitectura.md'),constants.COPYFILE_EXCL);
console.log(JSON.stringify(result));
