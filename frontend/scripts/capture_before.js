import puppeteer from "puppeteer-core";
import fs from "fs";
import path from "path";

const CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const BASE_URL = "http://localhost:5173";
const OUT_DIR = path.resolve(process.cwd(), "../docs/ui");

if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

async function capture() {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--window-size=1400,900"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 900 });

  console.log("Navigating to login page...");
  await page.goto(BASE_URL, { waitUntil: "networkidle0" });
  await page.screenshot({ path: path.join(OUT_DIR, "before_00_login.png") });

  const users = [
    { email: "admin@demo.law", label: "admin", isAdmin: true },
    { email: "partner@demo.law", label: "partner", isAdmin: false },
    { email: "associate@demo.law", label: "associate", isAdmin: false },
  ];

  for (const user of users) {
    console.log(`Testing user: ${user.email}`);
    await page.goto(BASE_URL, { waitUntil: "networkidle0" });

    // Click demo account button
    const buttons = await page.$$("button");
    let clicked = false;
    for (const btn of buttons) {
      const text = await page.evaluate(el => el.textContent, btn);
      if (text && text.includes(user.email)) {
        await btn.click();
        clicked = true;
        break;
      }
    }

    if (!clicked) {
      console.log(`Could not find button for ${user.email}, typing manually`);
      await page.type('input[type="email"]', user.email);
      await page.click('button[type="submit"]');
    }

    // Wait for the main page to load
    await page.waitForSelector("#nav-item-today", { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1500));

    // Capture Today page
    await page.screenshot({ path: path.join(OUT_DIR, `before_${user.label}_01_today.png`) });

    // Click Clients nav
    const clientsBtn = await page.$("#nav-item-clients");
    if (clientsBtn) {
      await clientsBtn.click();
      await new Promise(r => setTimeout(r, 1000));
      await page.screenshot({ path: path.join(OUT_DIR, `before_${user.label}_02_clients.png`) });

      // Click first client row
      const firstRow = await page.$("table tbody tr");
      if (firstRow) {
        await firstRow.click();
        await new Promise(r => setTimeout(r, 1000));
        await page.screenshot({ path: path.join(OUT_DIR, `before_${user.label}_03_client_detail.png`) });
      }
    }

    // Click Matters nav
    const mattersBtn = await page.$("#nav-item-matters");
    if (mattersBtn) {
      await mattersBtn.click();
      await new Promise(r => setTimeout(r, 1000));
      await page.screenshot({ path: path.join(OUT_DIR, `before_${user.label}_04_matters.png`) });

      if (user.isAdmin) {
        const allBtns = await page.$$("button");
        for (const b of allBtns) {
          const t = await page.evaluate(el => el.textContent, b);
          if (t && t.includes("Import Cases")) {
            await b.click();
            await new Promise(r => setTimeout(r, 1000));
            await page.screenshot({ path: path.join(OUT_DIR, `before_${user.label}_06_import.png`) });
            // Click back
            for (const b2 of await page.$$("button")) {
              const t2 = await page.evaluate(el => el.textContent, b2);
              if (t2 && t2.includes("Back")) {
                await b2.click();
                await new Promise(r => setTimeout(r, 500));
                break;
              }
            }
            break;
          }
        }
      }

      // Click first matter row
      const firstMatter = await page.$("table tbody tr");
      if (firstMatter) {
        await firstMatter.click();
        await new Promise(r => setTimeout(r, 1000));
        await page.screenshot({ path: path.join(OUT_DIR, `before_${user.label}_05_matter_detail.png`) });
      }
    }

    // Logout
    const allButtons = await page.$$("button");
    for (const b of allButtons) {
      const text = await page.evaluate(el => el.textContent, b);
      if (text && text.includes("Logout")) {
        await b.click();
        break;
      }
    }
    await new Promise(r => setTimeout(r, 1000));
  }

  await browser.close();
  console.log("SUCCESS: All before screenshots captured!");
}

capture().catch(err => {
  console.error("Error during capture:", err);
  process.exit(1);
});
