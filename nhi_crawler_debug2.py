import asyncio
from playwright.async_api import async_playwright

async def get_row():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating...")
        await page.goto('https://info.nhi.gov.tw/INAE3000/INAE3000S01')
        
        input_locator = page.get_by_placeholder('請輸入部分中英文名稱')
        await input_locator.fill('ACETAMINOPHEN')
        print("Clicking search...")
        button_locator = page.get_by_text('查詢', exact=True)
        await button_locator.click()
        
        print("Waiting for results...")
        await page.wait_for_selector('table tbody tr')
        await page.wait_for_timeout(2000)
        
        row_html = await page.locator('table tbody tr').first.inner_html()
        
        with open("first_row.txt", "w", encoding="utf-8") as f:
            f.write(row_html)
            
        print("Done. Saved to first_row.txt")
        await browser.close()

asyncio.run(get_row())
