document.documentElement.classList.add('js');

// Komşunu Bul: Çankırı turu (tahtadaki kural: ilk deneme 100, yanlıştan sonra 50)
(function(){
  const T=window.TURKIYE,svg=document.getElementById('harita');if(!T||!svg)return;
  const NS='http://www.w3.org/2000/svg',MERKEZ='TR-18',hedef=new Set(T.cankiri);
  svg.setAttribute('viewBox',`0 0 ${T.w} ${T.h}`);
  const ad=Object.fromEntries(T.il.map(p=>[p.id,p.n]));
  const kutular=[...document.querySelectorAll('#komsular li')];
  let bulunan=[],puan=0,hata=false;
  for(const p of T.il){
    const yol=document.createElementNS(NS,'path');
    yol.setAttribute('d',p.d);yol.dataset.id=p.id;
    if(p.id===MERKEZ){yol.classList.add('merkez');}
    else{yol.setAttribute('tabindex','0');yol.setAttribute('role','button');yol.setAttribute('aria-label',p.n);}
    svg.appendChild(yol);
  }
  const m=T.il.find(p=>p.id===MERKEZ),et=document.createElementNS(NS,'text');
  et.setAttribute('x',m.c[0]);et.setAttribute('y',m.c[1]+4);et.textContent='Çankırı';svg.appendChild(et);
  const geri=document.getElementById('geri');
  function yaz(){
    document.getElementById('puan').textContent=puan;
    document.getElementById('bulunan').textContent=bulunan.length;
    kutular.forEach((li,i)=>{li.textContent=bulunan[i]?ad[bulunan[i]]:'?';li.classList.toggle('bulundu',!!bulunan[i]);});
  }
  function sec(id){
    if(id===MERKEZ||bulunan.length===6)return;
    const yol=svg.querySelector(`path[data-id="${id}"]`);
    if(hedef.has(id)){
      if(bulunan.includes(id)){geri.textContent=ad[id]+' zaten bulundu.';geri.className='geri';return;}
      const p=hata?50:100;puan+=p;hata=false;bulunan.push(id);yol.classList.add('dogru');
      geri.textContent=bulunan.length===6?`Altı komşunun hepsi bulundu. Toplam ${puan} puan.`:`Doğru: ${ad[id]}. +${p} puan`;geri.className='geri iyi';
    }else{
      hata=true;yol.classList.add('yanlis');setTimeout(()=>yol.classList.remove('yanlis'),900);
      geri.textContent=`${ad[id]} Çankırı’ya komşu değil. Bir sonraki doğru 50 puan.`;geri.className='geri kotu';
    }
    yaz();
  }
  svg.addEventListener('click',e=>{const id=e.target.dataset&&e.target.dataset.id;if(id)sec(id);});
  svg.addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&e.target.dataset.id){e.preventDefault();sec(e.target.dataset.id);}});
  document.getElementById('yeniden').addEventListener('click',()=>{
    bulunan=[];puan=0;hata=false;svg.querySelectorAll('.dogru').forEach(p=>p.classList.remove('dogru'));
    geri.textContent='Yeni tur: Çankırı’nın altı komşusu.';geri.className='geri';yaz();
  });
})();

// Bir ders saatinde: kaydırma düğmeleri ve ilerleme çubuğu
(function(){
  const sira=document.getElementById('akis-sira'),cubuk=document.getElementById('akis-ilerleme');if(!sira)return;
  const adim=()=>sira.querySelector('li').getBoundingClientRect().width+32;
  document.getElementById('geri-kay').onclick=()=>sira.scrollBy({left:-adim(),behavior:'smooth'});
  document.getElementById('ileri-kay').onclick=()=>sira.scrollBy({left:adim(),behavior:'smooth'});
  const guncelle=()=>{const m=sira.scrollWidth-sira.clientWidth;const o=m>0?sira.clientWidth/sira.scrollWidth:1;cubuk.style.width=(o+(1-o)*(m>0?sira.scrollLeft/m:0))*100+'%';};
  sira.addEventListener('scroll',guncelle,{passive:true});addEventListener('resize',guncelle);guncelle();
})();

// Girişler: her bölümün parçaları sırayla
(function(){
  const gruplar=[['.pafta',['h1','.giris','.kunye','.levha']],['.dene',['h2','.dene-metin>p','.komsular','.harita-kagit']],['.fisler',['.fis-metin','.fis']],['.menu-alani',['.menu-kagit','.menu-levha']],['.akis',['h2','.akis-dugmeler','.akis-sira li']],['.mektup-alani',['.mektup','.koparma']],['.sss',['h2','.olgular','details','.sss-gorsel img']]];
  const gozcu=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.querySelectorAll('.gir').forEach(x=>x.classList.add('gorundu'));e.target.classList.add('gorundu');gozcu.unobserve(e.target);}}),{threshold:.12});
  for(const [b,parcalar] of gruplar){const k=document.querySelector(b);if(!k)continue;let i=0;
    for(const s of parcalar)k.querySelectorAll(s).forEach(x=>{x.classList.add('gir');x.style.setProperty('--gec',Math.min(i++,8)*75+'ms');});
    gozcu.observe(k);}
})();
