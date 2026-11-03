import type {RenderMode} from './api';
export function detectCapabilities():RenderMode{
 const canvas=document.createElement('canvas');
 try{const gl=canvas.getContext('webgl2',{antialias:false,failIfMajorPerformanceCaveat:true});if(!gl)return 'SAFE';const info=gl.getExtension('WEBGL_debug_renderer_info');const renderer=info?String(gl.getParameter(info.UNMASKED_RENDERER_WEBGL)):'';gl.getExtension('WEBGL_lose_context')?.loseContext();return /swiftshader|llvmpipe|Intel|HD Graphics/i.test(renderer)||navigator.hardwareConcurrency<=4?'LITE':'FULL';}catch{return 'SAFE';}
}
export async function sampleFrameTime():Promise<number>{
 return new Promise(resolve=>{let previous=performance.now(),sum=0,count=0,finished=false;const timer=setTimeout(()=>{finished=true;resolve(100);},1200);const frame=(now:number)=>{if(finished)return;sum+=now-previous;previous=now;if(++count>=10){finished=true;clearTimeout(timer);resolve(sum/count);}else requestAnimationFrame(frame);};requestAnimationFrame(frame);});
}
