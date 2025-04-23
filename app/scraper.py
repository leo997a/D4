from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def scrape_whoscored(url: str) -> dict:
    async with async_playwright() as p:
        try:
            # تشغيل المتصفح في وضع headless
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # الذهاب إلى الرابط
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # الانتظار حتى تحميل عنصر معين
            await page.wait_for_selector("div#match-centre-stats", timeout=15000)

            # استخراج البيانات
            stats = await page.evaluate("""
                () => {
                    const data = {};
                    const teams = document.querySelectorAll('div#match-centre-stats div.team-stats');
                    teams.forEach((team, index) => {
                        const teamName = team.querySelector('h3').innerText;
                        const statsItems = team.querySelectorAll('li');
                        const teamStats = {};
                        statsItems.forEach(item => {
                            const statName = item.querySelector('span.stat').innerText;
                            const statValue = item.querySelector('span.value').innerText;
                            teamStats[statName] = statValue;
                        });
                        data[`team_${index + 1}`] = { name: teamName, stats: teamStats };
                    });
                    return data;
                }
            """)

            await browser.close()
            return stats

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            await browser.close()
            return {"error": str(e)}
