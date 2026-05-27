import asyncio
from playwright.async_api import async_playwright, Browser, Page
import json
import logging

logger = logging.getLogger(__name__)


async def scrape_nhi_drug_info(drug_name: str, browser: Browser = None) -> dict:
    """
    爬取單一藥物的 NHI/TFDA 詳細資訊。

    Args:
        drug_name: 藥物名稱
        browser: 可選，已啟動的 Browser 實例（A3-1 重構：外部注入以重用）
                 若未提供則自行啟動/關閉

    Returns:
        dict with status/details or error
    """
    own_browser = browser is None
    pw_ctx = None

    try:
        if own_browser:
            pw_ctx = await async_playwright().start()
            browser = await pw_ctx.chromium.launch(headless=True)

        page = await browser.new_page()

        try:
            # Navigate to the NHI drug search page
            await page.goto(
                "https://info.nhi.gov.tw/INAE3000/INAE3000S01", timeout=30000
            )

            # Fill the drug name in the correct input field (placeholder "請輸入部分中英文名稱")
            input_locator = page.get_by_placeholder("請輸入部分中英文名稱")
            await input_locator.fill(drug_name)

            # Click the search button ("查詢")
            button_locator = page.get_by_text("查詢", exact=True)
            await button_locator.click()

            # A3-2: 等待結果載入（取代 wait_for_timeout(3000)）
            try:
                await page.wait_for_selector(
                    "table tbody tr, :text('無資料')", timeout=10000
                )
            except Exception:
                pass  # 超時則繼續檢查

            # Check if there are no results
            no_data = await page.get_by_text("無資料").count()
            if no_data > 0:
                await page.close()
                if own_browser:
                    await browser.close()
                    if pw_ctx:
                        await pw_ctx.stop()
                return {"status": "success", "results": []}

            # Extract table data
            try:
                await page.wait_for_selector("table tbody tr", timeout=5000)
            except Exception:
                await page.close()
                if own_browser:
                    await browser.close()
                    if pw_ctx:
                        await pw_ctx.stop()
                return {"status": "success", "results": []}

            rows = await page.locator("table tbody tr").all()
            if not rows:
                await page.close()
                if own_browser:
                    await browser.close()
                    if pw_ctx:
                        await pw_ctx.stop()
                return {"status": "success", "results": []}

            # Click the first drug's ID link to get to the details page
            first_row = rows[0]
            cells = await first_row.locator("td").all()
            drug_id = await cells[0].inner_text()
            drug_id = drug_id.strip()

            # The NHI drug ID link actually points to am external TFDA page
            href = await first_row.locator("a").first.get_attribute("href")

            # Navigate to the detail page
            if href:
                if href.startswith("/"):
                    href = "https://info.nhi.gov.tw" + href
                await page.goto(href)
                # A3-2: 等待頁面載入完成（取代 wait_for_timeout(5000)）
                await page.wait_for_load_state("domcontentloaded")

                # A3-3: 移除 debug 寫檔
                page_text = await page.locator("body").inner_text()

            details = {"id": drug_id, "source_url": href}

            try:
                # Based on TFDA detail layout, we grab all text and look for specific lines
                page_text = await page.locator("body").inner_text()

                # 要抓取的欄位（不帶冒號，用於輸出 key）
                markers = [
                    "中文品名",
                    "英文品名",
                    "適應症",
                    "藥品類別",
                    "主成分略述",
                    "劑型",
                    "藥商名稱",
                    "製造廠名稱",
                    "許可證種類",
                    "有效日期",
                    "包裝",
                    "管制藥品分類級別",
                ]
                # 頁面上的格式帶全形冒號，例如 "中文品名：" 或 "中文品名：\n肌絡舒片"
                lines = page_text.split("\n")

                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    for marker in markers:
                        # 比對帶冒號的格式，例如 "中文品名：" 或 "中文品名:"
                        if (
                            line_stripped == marker + "："
                            or line_stripped == marker + ":"
                        ):
                            # 值在下一個非空行
                            for j in range(i + 1, len(lines)):
                                next_line = lines[j].strip()
                                if next_line and not any(
                                    next_line == m + "：" or next_line == m + ":"
                                    for m in markers
                                ):
                                    details[marker] = next_line
                                    break
                            break
                        elif line_stripped.startswith(
                            marker + "："
                        ) or line_stripped.startswith(marker + ":"):
                            # 值在同一行冒號後面，例如 "中文品名：肌絡舒片"
                            sep = "：" if "：" in line_stripped else ":"
                            value = line_stripped.split(sep, 1)[1].strip()
                            if value and value != "--":
                                details[marker] = value
                            break

                # Try to get images (TFDA usually has a tab for 仿單/外盒標籤/藥品外觀)
                try:
                    # Look for the tab and click it
                    tab = page.get_by_text("仿單/外盒標籤/藥品外觀", exact=False)
                    if await tab.count() > 0:
                        await tab.first.click()
                        # A3-2: 等待圖片載入（取代 wait_for_timeout(2000)）
                        try:
                            await page.wait_for_selector("img", timeout=3000)
                        except Exception:
                            pass

                        images = await page.locator("img").all()
                        img_urls = []
                        for img in images:
                            src = await img.get_attribute("src")
                            if src and (
                                "DOH" in src or "fda.gov.tw" in src or "DRPIQ" in src
                            ):
                                if src.startswith("/"):
                                    src = "https://lmspiq.fda.gov.tw" + src
                                img_urls.append(src)

                        if img_urls:
                            # Filter out common UI icons if possible
                            img_urls = [
                                u
                                for u in img_urls
                                if "icon" not in u.lower() and "logo" not in u.lower()
                            ]
                            details["images"] = list(set(img_urls))
                except Exception as e:
                    details["image_error"] = str(e)

            except Exception as e:
                details["error_extracting"] = str(e)

            await page.close()
            if own_browser:
                await browser.close()
                if pw_ctx:
                    await pw_ctx.stop()
            return {"status": "success", "details": details}

        except Exception as e:
            try:
                await page.close()
            except Exception:
                pass
            if own_browser:
                try:
                    await browser.close()
                except Exception:
                    pass
                if pw_ctx:
                    await pw_ctx.stop()
            return {"error": str(e)}
    except Exception as e:
        if own_browser and pw_ctx:
            try:
                await pw_ctx.stop()
            except Exception:
                pass
        return {"error": str(e)}


if __name__ == "__main__":
    result = asyncio.run(
        scrape_nhi_drug_info("普拿疼")
    )  # Switching back to a common name to test generic search if possible, or sticking to ACETAMINOPHEN
    if not result.get("details"):  # if it fails, try the active generic name
        print("Failed with 普拿疼, trying ACETAMINOPHEN")
        result = asyncio.run(scrape_nhi_drug_info("ACETAMINOPHEN"))
    print(json.dumps(result, indent=2, ensure_ascii=False))
