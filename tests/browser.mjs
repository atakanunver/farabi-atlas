import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const browser=await chromium.launch({executablePath:'/usr/bin/chromium-browser',headless:true,args:['--no-sandbox']});
const context=await browser.newContext({viewport:{width:1440,height:1000}});
const external=[],errors=[];
await context.route('**/*',route=>{const url=new URL(route.request().url());if(url.hostname!=='127.0.0.1'){external.push(url.origin);return route.abort();}return route.continue();});
const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...rest){return kind.startsWith('webgl')?null:original.call(this,kind,...rest);};});
const catalog=JSON.parse(fs.readFileSync('public/data/catalog.json','utf8'));
const questions=JSON.parse(fs.readFileSync('public/data/questions.json','utf8'));
const getSession=()=>page.evaluate(async()=>{const id=localStorage.getItem('atlas-session');return id?fetch('/api/atlas/sessions/'+id).then(r=>r.json()):null;});
try{
 await page.goto('http://127.0.0.1:8099/kure/');await page.waitForFunction(()=>document.querySelector('#start')?.disabled===false);
 await page.locator('.ocean-sphere').waitFor();assert.ok(await page.locator('.kind-country.target').count()>190);await page.locator('#turkey').click();assert.equal(await page.locator('.kind-province.target').count(),81);
 fs.mkdirSync('test-results',{recursive:true});await page.screenshot({path:'test-results/desktop.png',fullPage:true});
 await page.locator('#world').click();await page.locator('#globe').click();assert.equal(await page.locator('.ocean-sphere').count(),1);
 await page.screenshot({path:'test-results/globe.png',fullPage:true});
 await page.locator('#flat').click();await page.locator('#turkey').click();
 for(const game of ['turkiye','komsu','bolge','dunya','tarih']){
  await page.locator('#games-tab').click();await page.locator('#game').selectOption(game);await page.locator('#count').selectOption('5');await page.locator('#seconds').selectOption('0');
  if(game==='dunya')await page.locator('#category').selectOption('river');
  await page.locator('#start').click();await page.locator('#question-banner').waitFor({state:'visible'});
  let attempts=0;
  while(attempts++<30){
   const s=await getSession();if(!s||s.done)break;
   let targets;
   if(game==='komsu')targets=catalog.features.find(f=>f.properties.id===s.question.anchor).properties.neighbors;
   else if(game==='bolge'){const region=s.question.prompt.split(' Bölgesi')[0];targets=catalog.features.filter(f=>f.properties.type==='province'&&f.properties.region===region).map(f=>f.properties.id);}
   else targets=questions.find(q=>q.id===s.question.id).targetIds;
   const target=targets.find(id=>!s.selected.includes(id));
   await page.locator(`.target[data-id="${target}"]`).first().dispatchEvent('pointerdown',{clientX:0,clientY:0});
   await page.locator(`.target[data-id="${target}"]`).first().dispatchEvent('pointerup',{clientX:0,clientY:0});
   await page.waitForTimeout(800);
  }
  await page.locator('#dialog[open]').waitFor();assert.match(await page.locator('#dialog-body').innerText(),/puan/);await page.locator('#close-dialog').click();
 }
 for(const [width,height]of [[768,1024],[390,844]]){
  await page.setViewportSize({width,height});await page.screenshot({path:`test-results/${width}.png`,fullPage:true});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'horizontal overflow');
 }
 assert.deepEqual(external,[]);assert.deepEqual(errors,[]);console.log('PASS: 5 complete games, globe, 3 widths, no external requests or browser errors');
}finally{await browser.close();}
