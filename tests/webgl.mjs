import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
const browser=await chromium.launch({executablePath:'/usr/bin/chromium-browser',headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const external=[],errors=[];
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 page.on('pageerror',e=>errors.push(e.message));
 page.on('console',m=>{if(m.type()==='error')errors.push(m.text());if(m.type()==='warning')console.log('Browser:',m.text());});
 await page.route('**/*',r=>{const u=new URL(r.request().url());if(u.hostname!=='127.0.0.1'){external.push(u.href);return r.abort();}return r.continue();});
 await page.goto('http://127.0.0.1:8099/kure/?render=LITE');await page.waitForFunction(()=>document.querySelector('#start')?.disabled===false);
 await page.waitForTimeout(1500);
 const mode=await page.locator('#render-mode').innerText();
 assert.match(mode,/LITE/,'WebGL unexpectedly fell back: '+JSON.stringify(errors));
 await page.screenshot({path:'test-results/webgl.png',fullPage:true});
 await page.locator('#world').click();await page.locator('#globe').click();await page.waitForTimeout(2000);
 await page.screenshot({path:'test-results/webgl-globe.png',fullPage:true});
 const ranges=await page.evaluate(async()=>{const r=await fetch('/kure/data/world-lite.pmtiles',{headers:{Range:'bytes=0-126'}});return {status:r.status,length:(await r.arrayBuffer()).byteLength};});
 assert.deepEqual(ranges,{status:206,length:127});assert.deepEqual(external,[]);assert.deepEqual(errors,[]);
 await page.locator('#safe').click();await page.locator('.safe-map').waitFor();assert.equal(await page.locator('.ocean-sphere').count(),1);
 // Locate any accidental world-covering country in Mercator to prevent a blank-looking map.
 await page.locator('#flat').click();await page.locator('#turkey').click();
 const covering=await page.evaluate(()=>{const svg=document.querySelector('.safe-map');const point=new DOMPoint(400,80);return [...svg.querySelectorAll('.land')].filter(n=>n.isPointInFill(point)).map(n=>n.getAttribute('data-feature'));});
 console.log('Mercator top coverage:',covering);
 console.log('PASS: WebGL LITE, local PMTiles byte ranges, globe and runtime SAFE fallback; no external requests');
}finally{await browser.close();}
