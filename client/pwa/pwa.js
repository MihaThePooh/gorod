// Installation adds a standalone window; the shared world still needs a connection.
(()=>{
 let prompt=null;const button=document.querySelector('#installTown'),dialog=document.querySelector('#installHelp');
 const standalone=()=>matchMedia('(display-mode: standalone)').matches||navigator.standalone;
 function help(){document.querySelector('#installText').textContent=/iPhone|iPad|iPod/.test(navigator.userAgent)?'В Safari нажми «Поделиться», затем «На экран Домой».':'Открой меню браузера и выбери «Установить приложение» или «Добавить на главный экран». Если пункта нет, попробуй Chrome или Edge.';dialog.showModal()}
 button.hidden=standalone();button.onclick=async()=>{if(prompt){const current=prompt;prompt=null;await current.prompt();await current.userChoice}else help()};
 document.querySelector('#closeInstall').onclick=()=>dialog.close();
 addEventListener('beforeinstallprompt',e=>{e.preventDefault();prompt=e;if(!standalone())button.hidden=false});
 addEventListener('appinstalled',()=>{button.hidden=true;dialog.close()});
 if('serviceWorker'in navigator)navigator.serviceWorker.register('./sw.js',{scope:'./'}).catch(()=>{});
 if(new URL(location.href).searchParams.has('install')&&!standalone())help();
})();
