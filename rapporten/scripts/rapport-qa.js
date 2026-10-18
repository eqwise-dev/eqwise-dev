// Controleert een EQwise-rapport (HTML) op alle vaste schermbreedtes en maakt de A4-PDF.
//
// Gebruik:
//   npm i playwright-core
//   node rapporten/scripts/rapport-qa.js <rapport.html> <uitmap>
//
// Uitvoer in <uitmap>: schermafdrukken per breedte en <naam>.pdf. Elke breedte draait ook met een
// donkere apparaatinstelling; het rapport hoort dan wit te blijven (geen donkere modus).
// Het script meldt per breedte de scrollbreedte; die moet gelijk zijn aan de schermbreedte.
// Elementen in .tabel en pre mogen binnen hun eigen scrollvak breder zijn.

const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright-core');

const BREEDTES = [320, 375, 390, 430, 768, 1024, 1280, 1440, 1920];
const CHROMIUM = process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';

(async () => {
  const [bron, uit] = process.argv.slice(2);
  if (!bron || !uit) { console.error('Gebruik: node rapport-qa.js <rapport.html> <uitmap>'); process.exit(2); }
  fs.mkdirSync(uit, { recursive: true });
  const url = 'file://' + path.resolve(bron);
  const naam = path.basename(bron, '.html');
  const opties = fs.existsSync(CHROMIUM) ? { executablePath: CHROMIUM } : {};
  const browser = await chromium.launch(opties);
  let fouten = 0;

  for (const breedte of BREEDTES) {
    for (const schema of ['light', 'dark']) {
      const pagina = await browser.newPage({ viewport: { width: breedte, height: 900 }, colorScheme: schema });
      await pagina.goto(url);
      await pagina.waitForTimeout(500);
      const meting = await pagina.evaluate((w) => ({
        scrollbreedte: document.documentElement.scrollWidth,
        te_breed: [...document.querySelectorAll('body *')]
          .filter((el) => el.getBoundingClientRect().right > w + 1 && !el.closest('.tabel, pre'))
          .slice(0, 5)
          .map((el) => el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : '')),
      }), breedte);
      const goed = meting.scrollbreedte <= breedte && meting.te_breed.length === 0;
      if (!goed) fouten++;
      console.log(`${goed ? 'ok  ' : 'FOUT'} ${breedte} ${schema} scrollbreedte=${meting.scrollbreedte}` + (meting.te_breed.length ? ` te breed: ${meting.te_breed.join(', ')}` : ''));
      await pagina.screenshot({ path: path.join(uit, `${naam}_${breedte}_${schema}.png`), fullPage: schema === 'light' && (breedte === 1440 || breedte === 390) });
      await pagina.close();
    }
  }

  const print = await browser.newPage({ viewport: { width: 760, height: 1000 } });
  await print.goto(url);
  await print.waitForTimeout(500);
  await print.pdf({ path: path.join(uit, `${naam}.pdf`), format: 'A4', printBackground: true, scale: 0.9, margin: { top: '12mm', bottom: '12mm' } });
  console.log(`pdf  ${path.join(uit, naam + '.pdf')}`);

  await browser.close();
  process.exit(fouten ? 1 : 0);
})();
