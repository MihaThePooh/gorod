// Hub keeps credentials in HttpOnly cookies. Never persist tokens in game storage.
const meta=name=>document.querySelector(`meta[name="${name}"]`)?.content;
export const accountMode=meta('town-auth')==='hub';
const id=meta('hub-id'),home=meta('hub-home');
let refreshing=null,redirecting=false;
export function login(){
 if(redirecting)return;redirecting=true;
 const next=new URL(location.href);next.searchParams.delete('town');
 location.replace(`${home}/?app=town&next=${encodeURIComponent(next.href)}`);
}
async function refresh(){
 if(!refreshing)refreshing=fetch(`${id}/api/auth/refresh`,{method:'POST',credentials:'include'}).finally(()=>{refreshing=null});
 return refreshing;
}
export async function hubFetch(url,options={}){
 let response=await fetch(url,{...options,credentials:'include'});
 if(response.status!==401&&response.status!==403)return response;
 const renewed=await refresh();
 if(renewed.ok)return fetch(url,{...options,credentials:'include'});
 if(renewed.status===401){login();throw Error('Нужно войти через хаб.');}
 throw Error('Сервис входа временно недоступен. Попробуй ещё раз.');
}
