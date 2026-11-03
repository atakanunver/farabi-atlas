export interface Config {game:string;category:string;count:number;seconds:number;difficulty:string}
export interface Question {id:string;prompt:string;layers:import('../map/api').Kind[];scope:'turkey'|'world';anchor?:string;required?:number}
export interface Session {id:string;config:Config;className:string;index:number;total:number;question:Question|null;score:number;streak:number;attempts:number;selected:string[];revision:number;paused:boolean;remaining:number|null;done:boolean;feedback?:{status:string;message:string;selected?:string;points?:number;answers?:string[]};events:{prompt:string;correct:boolean;points:number}[]}
export interface Context {teacher:string;classes:string[];csrf:string;demo:boolean}
export class ExistingGameBackendAdapter{
 context!:Context;
 async init(){this.context=await this.request<Context>('/context');return this.context;}
 async request<T>(path:string,body?:Record<string,string>):Promise<T>{const response=await fetch('/api/atlas'+path,{credentials:'same-origin',...(body?{method:'POST',body:new URLSearchParams({...body,csrf:this.context.csrf})}:{})});if(!response.ok){let message='Farabi bağlantısı kurulamadı.';try{const data=await response.json();message=typeof data.detail==='string'?data.detail:message;}catch{}throw new Error(message);}if(!response.headers.get('content-type')?.includes('application/json'))throw new Error('Dijital Okul oturumunuz sona erdi; yeniden giriş yapın.');return response.json();}
 start(className:string,config:Config){return this.request<Session>('/sessions',{className,config:JSON.stringify(config)});}
 action(s:Session,action:string,selected?:string){return this.request<Session>(`/sessions/${s.id}/action`,{action,revision:String(s.revision),...(selected?{selected}:{})});}
 get(id:string){return this.request<Session>('/sessions/'+id);}
 history(){return this.request<{id:string;className:string;created:number;finished:number|null;score:number}[]>('/sessions');}
}
