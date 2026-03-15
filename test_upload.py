import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🌍 開啟首頁...")
        await page.goto("http://127.0.0.1:5000/")
        
        prescription_path = r"D:\大學\專題\測試資料\螢幕擷取畫面 2025-10-22 070659.png"
        drug_image_path = r"D:\大學\專題\測試資料\衛部藥製字第059239號.jpg"
        
        # 1. 測試藥單辨識
        print(f"📄 測試藥單辨識: {prescription_path}")
        await page.click("button >> text='📄 拍攝藥單辨識'")
        await page.wait_for_selector("#prescriptionUploadArea")
        
        # 設置 input files
        await page.locator("#prescriptionImageInput").set_input_files(prescription_path)
        await page.wait_for_selector("#prescriptionImagePreview", state="visible")
        
        # 點擊上傳
        await page.click("#prescriptionUploadBtn")
        
        print("⏳ 等待辨識結果...")
        # 等待讀取畫面消失並且出現結果
        await page.wait_for_selector(".result-item", timeout=60000)
        await asyncio.sleep(2) # 讓動畫跑完
        
        res1_screenshot = os.path.join(os.getcwd(), '測試截圖_藥單結果.png')
        await page.screenshot(path=res1_screenshot)
        print(f"📸 藥單結果已擷圖: {res1_screenshot}")
        
        # 點擊第一個藥物查看詳情
        print("🔍 點擊查看藥物詳細資訊...")
        await page.click(".result-item >> nth=0")
        await page.wait_for_selector(".detail-info", timeout=30000)
        await asyncio.sleep(3) # 等待爬蟲可能回傳
        
        res2_screenshot = os.path.join(os.getcwd(), '測試截圖_藥單單一藥物詳情.png')
        await page.screenshot(path=res2_screenshot)
        print(f"📸 藥物詳情已擷圖: {res2_screenshot}")
        
        # 點擊返回直到首頁
        print("🏠 返回首頁...")
        await page.click("button:visible >> text='← 返回'")
        await asyncio.sleep(1)
        await page.click("button:visible >> text='← 返回首頁'")
        await asyncio.sleep(1)
        
        # 2. 測試單一藥物辨識
        print(f"📷 測試單一藥物辨識: {drug_image_path}")
        await page.click("button >> text='📷 拍照辨識藥物'")
        await page.wait_for_selector("#uploadArea")
        
        await page.locator("#imageInput").set_input_files(drug_image_path)
        await page.wait_for_selector("#imagePreview", state="visible")
        
        await page.click("#uploadBtn")
        
        print("⏳ 等待辨識結果...")
        await page.wait_for_selector(".result-item", timeout=60000)
        await asyncio.sleep(2)
        
        res3_screenshot = os.path.join(os.getcwd(), '測試截圖_單一藥物結果.png')
        await page.screenshot(path=res3_screenshot)
        print(f"📸 單一藥物結果已擷圖: {res3_screenshot}")
        
        await browser.close()
        print("✅ 測試完成！")

if __name__ == "__main__":
    asyncio.run(main())
