import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
const browser=await chromium.launch({executablePath:'/usr/bin/chromium-browser',headless:true,args:['--no-sandbox']});
try{
 const page=await browser.newPage();const errors=[],external=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>{if(new URL(r.request().url()).hostname!=='127.0.0.1'){external.push(r.request().url());return r.abort();}return r.continue();});
 for(const[width,height]of [[1440,900],[768,1024],[390,844]]){
  await page.setViewportSize({width,height});await page.goto('http://127.0.0.1:8099/kure/');await page.locator('.ocean-sphere').waitFor();
  const state=await page.evaluate(()=>({drawn:[...document.querySelectorAll('.safe-map .target')].filter(n=>n.getAttribute('d')).length,width:document.querySelector('#map').clientWidth,height:document.querySelector('#map').clientHeight,overflow:document.documentElement.scrollWidth>innerWidth,panel:getComputedStyle(document.querySelector('.right-panel')).display}));
  assert.ok(state.drawn>60,'Map has not actually drawn visible geometry');assert.ok(state.width>=300&&state.height>=400);assert.equal(state.overflow,false);assert.equal(state.panel,'none');
  await page.screenshot({path:`test-results/redesign-${width}.png`,fullPage:true});
  await page.locator('#games-tab').click();await page.locator('.right-panel').waitFor({state:'visible'});await page.locator('#close-games').click();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 console.log('PASS: actual map geometry drawn at 1440/768/390, no overflow, game drawer controls, zero external requests');
}finally{await browser.close();}
