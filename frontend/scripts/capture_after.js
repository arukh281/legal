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
  await page.screenshot({ path: path.join(OUT_DIR, "after_00_login.png") });

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
      await page.type('input[type="email"]', user.email);
      await page.click('button[type="submit"]');
    }

    await page.waitForSelector("#nav-item-today", { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1200));

    // Capture Today page
    await page.screenshot({ path: path.join(OUT_DIR, `after_${user.label}_01_today.png`) });

    // Click Clients nav
    const clientsBtn = await page.$("#nav-item-clients");
    if (clientsBtn) {
      await clientsBtn.click();
      await new Promise(r => setTimeout(r, 1000));
      await page.screenshot({ path: path.join(OUT_DIR, `after_${user.label}_02_clients.png`) });

      // Click first client row
      const firstClientRow = await page.$(".table tbody tr.clickable");
      if (firstClientRow) {
        await firstClientRow.click();
        await new Promise(r => setTimeout(r, 1000));
        await page.screenshot({ path: path.join(OUT_DIR, `after_${user.label}_03_client_detail.png`) });
      }
    }

    // Click Matters nav
    const mattersBtn = await page.$("#nav-item-matters");
    if (mattersBtn) {
      await mattersBtn.click();
      await new Promise(r => setTimeout(r, 1000));
      await page.screenshot({ path: path.join(OUT_DIR, `after_${user.label}_04_matters.png`) });

      // Click first matter row to open Matter Detail
      const firstMatterRow = await page.$(".table tbody tr.clickable");
      if (firstMatterRow) {
        await firstMatterRow.click();
        await new Promise(r => setTimeout(r, 1000));
        await page.screenshot({ path: path.join(OUT_DIR, `after_${user.label}_05_matter_detail.png`) });

        if (user.isAdmin) {
          // Click Hearings tab
          const tabButtons = await page.$$(".tab-btn");
          for (const tb of tabButtons) {
            const tText = await page.evaluate(el => el.textContent, tb);
            if (tText && tText.includes("Hearings")) {
              await tb.click();
              await new Promise(r => setTimeout(r, 600));
              await page.screenshot({ path: path.join(OUT_DIR, `after_${user.label}_05_matter_detail_hearings.png`) });
            } else if (tText && tText.includes("Tasks")) {
              await tb.click();
              await new Promise(r => setTimeout(r, 600));
              await page.screenshot({ path: path.join(OUT_DIR, `after_${user.label}_05_matter_detail_tasks.png`) });
            } else if (tText && tText.includes("Documents")) {
              await tb.click();
              await new Promise(r => setTimeout(r, 600));
              await page.screenshot({ path: path.join(OUT_DIR, `after_${user.label}_05_matter_detail_documents.png`) });
            } else if (tText && tText.includes("Client updates")) {
              await tb.click();
              await new Promise(r => setTimeout(r, 600));
              await page.screenshot({ path: path.join(OUT_DIR, `after_${user.label}_05_matter_detail_client_updates.png`) });
            }
          }
        }
      }
    }

    // Click Tasks nav
    const tasksBtn = await page.$("#nav-item-tasks");
    if (tasksBtn) {
      await tasksBtn.click();
      await new Promise(r => setTimeout(r, 1000));
      await page.screenshot({ path: path.join(OUT_DIR, `after_${user.label}_06_tasks.png`) });
    }

    // If admin, click Import nav
    if (user.isAdmin) {
      const importBtn = await page.$("#nav-item-import");
      if (importBtn) {
        await importBtn.click();
        await new Promise(r => setTimeout(r, 1000));
        await page.screenshot({ path: path.join(OUT_DIR, `after_${user.label}_07_import.png`) });
      }
    }

    // Sign out
    const allButtons = await page.$$("button");
    for (const b of allButtons) {
      const text = await page.evaluate(el => el.textContent, b);
      if (text && text.includes("Sign out")) {
        await b.click();
        break;
      }
    }
    await new Promise(r => setTimeout(r, 1000));
  }

  await browser.close();
  console.log("SUCCESS: All after screenshots captured!");
}

capture().catch(err => {
  console.error("Error during capture:", err);
  process.exit(1);
});
