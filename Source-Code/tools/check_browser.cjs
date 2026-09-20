// Optional UI checks. Install Playwright separately; no solver dependencies.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const manual = path.resolve(process.argv[2] || path.join(__dirname, '..'));
const parameters = JSON.parse(fs.readFileSync(path.join(manual, 'docs-data/parameters.json')));
const mainCount = parameters.filter(row => row.program === 'main').length;
const results = process.argv[3] && path.resolve(process.argv[3]);
const resultData = results && JSON.parse(fs.readFileSync(path.join(results, 'docs-data/results.json')));
const output = path.resolve(process.argv[4] || '/tmp/hint-docs-browser');
fs.mkdirSync(output, {recursive:true});

(async () => {
  const browser = await chromium.launch({headless:true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
      ? {executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH} : {})});
  const report = [];
  try {
    for (const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
      const context = await browser.newContext({viewport, offline:true});
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(pathToFileURL(path.join(manual,'index.html')).href);
      assert.equal(await page.locator('.chapter').count(), await page.locator('#sidebar nav a').count());
      assert(await page.locator('.chapter').count() >= 18);
      assert(await page.locator('math').count() >= 15);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1));
      if (viewport.width < 760) await page.locator('#menu-toggle').click();
      await page.locator('#global-search').fill('eta1');
      assert(await page.locator('.chapter:visible').count() > 0);
      await page.locator('#global-search').fill('not-a-real-parameter-9876');
      assert(await page.locator('#no-results').isVisible());
      await page.locator('#global-search').fill('');
      if (viewport.width < 760) await page.locator('#menu-toggle').click();
      const mainTable = page.locator('#main-parameters');
      await mainTable.locator('.param-search').fill('eta1');
      assert.equal(await mainTable.locator('tbody tr:visible').count(),1);
      await mainTable.locator('.param-version').selectOption('wall');
      assert.equal(await mainTable.locator('tbody tr:visible').count(),0);
      await mainTable.locator('.param-search').fill('');
      await mainTable.locator('.param-version').selectOption('all');
      assert.equal(await mainTable.locator('tbody tr:visible').count(),mainCount);
      await mainTable.locator('.param-version').selectOption('different');
      assert(await mainTable.locator('tbody tr:visible').count() >= 1);
      await mainTable.locator('.param-version').selectOption('all');
      await page.evaluate(() => {
        document.documentElement.style.scrollBehavior = 'auto';
        document.querySelector('#main-parameters').scrollIntoView({block:'start',behavior:'instant'});
      });
      await page.screenshot({path:path.join(output,`manual-parameters-${viewport.width}.png`)});
      await page.evaluate(() => document.querySelector('#model').scrollIntoView({block:'start',behavior:'instant'}));
      await page.screenshot({path:path.join(output,`manual-equations-${viewport.width}.png`)});
      await page.locator('#overview').scrollIntoViewIfNeeded();
      await page.evaluate(() => scrollTo(0,0));
      await page.screenshot({path:path.join(output,`manual-${viewport.width}.png`)});
      assert.deepEqual(errors, []);
      report.push({site:'manual',viewport,errors,checks:'offline, layout, chapters, math, search, parameter versions'});
      if (results) {
        await page.goto(pathToFileURL(path.join(results,'index.html')).href);
        assert.equal(await page.locator('.figure-card').count(),resultData.figure_count);
        assert.equal(await page.locator('#initial-poincare').count(),1);
        await page.locator('#figure-search').fill('初始化总场');
        assert.equal(await page.locator('.figure-card:visible').count(),1);
        assert.equal(await page.locator('.figure-card:visible').getAttribute('data-id'),'poincare_total_initial_three_sections');
        await page.locator('.figure-card:visible .image-link').click();
        await page.locator('#viewer-image').evaluate(img => img.decode());
        assert(await page.locator('#viewer-title').innerText().then(text => text.includes('第 0 步')));
        await page.keyboard.press('Escape');
        await page.locator('#figure-search').fill('');
        await page.locator('[data-category="iota"].category-tab').click();
        assert.equal(await page.locator('.figure-card:visible').count(),5);
        await page.locator('#figure-search').fill('initial_vmec_s');
        assert.equal(await page.locator('.figure-card:visible').count(),1);
        await page.locator('.figure-card:visible .image-link').click();
        assert(await page.locator('#viewer').isVisible());
        await page.locator('#viewer-image').evaluate(img => img.decode());
        assert(await page.locator('#viewer-image').evaluate(img => img.naturalWidth>100));
        await page.screenshot({path:path.join(output,`result-viewer-${viewport.width}.png`)});
        await page.keyboard.press('Escape');
        assert(!(await page.locator('#viewer').isVisible()));
        await page.locator('#figure-search').fill('');
        await page.locator('.category-tab[data-category="all"]').click();
        await page.locator('#figure-search').fill('iota');
        assert.equal(await page.locator('.figure-card:visible').count(),5);
        await page.locator('#figure-search').fill('不存在-不存在');
        assert(await page.locator('#empty').isVisible());
        await page.locator('#figure-search').fill('');
        await page.evaluate(() => scrollTo(0,0));
        assert(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth+1));
        await page.locator('.figure-card img').first().evaluate(img => img.decode());
        await page.screenshot({path:path.join(output,`results-${viewport.width}.png`)});
        assert.deepEqual(errors, []);
        report.push({site:'results',viewport,errors,figureCount:resultData.figure_count,checks:'offline, initial versus evolved, filters, dialog, full PNG, escape, layout'});
      }
      await context.close();
    }
  } finally { await browser.close(); }
  fs.writeFileSync(path.join(output,'browser-report.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
})().catch(error => { console.error(error); process.exitCode=1; });
