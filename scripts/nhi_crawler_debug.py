from playwright.sync_api import sync_playwright
import time

def explore_nhi():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://info.nhi.gov.tw/INAE3000/INAE3000S01')
        page.wait_for_timeout(5000)
        
        # Log all text contents
        texts = page.locator('body').inner_text()
        print('--- PAGE TEXT ---')
        print(texts[:1000])
        
        # Find input fields
        inputs = page.locator('input').all()
        print('\n--- INPUT FIELDS ---')
        for i, inp in enumerate(inputs):
            try:
                name = inp.get_attribute('name') or ''
                id = inp.get_attribute('id') or ''
                placeholder = inp.get_attribute('placeholder') or ''
                print(f'Input {i}: id={id}, name={name}, placeholder={placeholder}')
            except:
                pass
                
        # Find buttons
        buttons = page.locator('button').all()
        print('\n--- BUTTONS ---')
        for i, btn in enumerate(buttons):
            try:
                text = btn.inner_text().strip()
                if text:
                    print(f'Button {i}: text=\"{text}\"')
            except:
                pass
                
        browser.close()

explore_nhi()
