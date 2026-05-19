import time
import os
import glob
from playwright.sync_api import sync_playwright
import imageio.v3 as iio

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            record_video_dir=".",
            record_video_size={"width": 1920, "height": 1080},
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        print("Opening Homepage...")
        page.goto("http://127.0.0.1:5000")
        page.wait_for_timeout(5000)
        page.screenshot(path="d:\\大學\\專題\\MUS2\\01_首頁.png")
        
        print("Testing Photo Recognition...")
        page.get_by_text("拍照辨識藥物").click()
        page.wait_for_timeout(2000)
        page.screenshot(path="d:\\大學\\專題\\MUS2\\02_拍照辨識_上傳.png")
        
        # Upload Image
        page.locator("#imageInput").set_input_files("d:\\大學\\專題\\MUS2\\medicine_photos\\內衛成製字第000075號_1.jpg")
        page.wait_for_timeout(2000)
        page.locator("#uploadBtn").click()
        
        print("Waiting for results...")
        page.wait_for_selector("#resultContent .result-item", timeout=30000)
        page.wait_for_timeout(5000)
        page.screenshot(path="d:\\大學\\專題\\MUS2\\03_拍照辨識_結果.png")
        
        print("Viewing details...")
        page.locator("#resultContent .result-item").first.click()
        page.wait_for_selector(".detail-info", timeout=30000)
        page.wait_for_timeout(5000)
        page.screenshot(path="d:\\大學\\專題\\MUS2\\06_藥物詳情.png", full_page=True)
        
        print("Returning Home...")
        page.evaluate("goToPage('homePage')")
        page.wait_for_timeout(2000)
        
        print("Testing Prescription Recognition...")
        page.evaluate("goToPage('prescriptionCapturePage')")
        page.wait_for_timeout(2000)
        
        page.locator("#prescriptionImageInput").set_input_files("d:\\大學\\專題\\MUS2\\uploads\\84a048f2-65be-4532-b959-2b6e0ca00d18_real_test.jpg")
        page.wait_for_timeout(2000)
        page.locator("#prescriptionUploadBtn").click()
        
        print("Waiting for prescription results...")
        page.wait_for_selector("#resultContent .result-item", timeout=30000)
        page.wait_for_timeout(5000)
        page.screenshot(path="d:\\大學\\專題\\MUS2\\04_藥單辨識_結果.png")
        
        page.evaluate("goToPage('homePage')")
        page.wait_for_timeout(2000)
        
        print("Testing Search...")
        page.evaluate("goToPage('searchPage')")
        page.wait_for_timeout(2000)
        page.locator("#searchInput").fill("普拿疼")
        page.wait_for_timeout(1000)
        page.locator("#searchBtn").click()
        
        page.wait_for_selector("#searchResults .result-item", timeout=30000)
        page.wait_for_timeout(5000)
        page.screenshot(path="d:\\大學\\專題\\MUS2\\05_搜尋結果.png", full_page=True)
        
        page.evaluate("goToPage('homePage')")
        page.wait_for_timeout(5000)
        
        # Save video
        video_path = page.video.path()
        context.close()
        browser.close()
        
        print(f"Video saved at {video_path}, now converting to MP4...")
        mp4_path = r"d:\大學\專題\MUS2\藥知道_Demo.mp4"
        
        # Convert webm to mp4
        import subprocess
        # Use imageio to write mp4 didn't support sound, but it's simpler. FFMPEG might be not installed system-wide but imageio-ffmpeg is.
        # Actually imageio does support using imageio.get_writer directly.
        try:
            reader = iio.imiter(video_path, plugin="pyav")
            writer = iio.iwrite(mp4_path, reader, plugin="pyav", codec="libx264", fps=30)
            with open(mp4_path, 'wb'):
                pass
        except:
            # Fallback to imageio v2 style
            import imageio
            reader = imageio.get_reader(video_path)
            fps = reader.get_meta_data().get('fps', 30)
            writer = imageio.get_writer(mp4_path, fps=fps)
            for im in reader:
                writer.append_data(im)
            writer.close()
            
        print("Process completed! mp4 at", mp4_path)

if __name__ == "__main__":
    main()
