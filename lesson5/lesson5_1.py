import os
from playwright.sync_api import sync_playwright


def get_html_path(): 
    """回傳html檔案的絕對路徑"""
    current_dir=os.path.dirname(os.path.abspath(__file__)) #abspath當前檔案絕對路徑(含檔案)，dirname
    html_path=os.path.join(current_dir,"waiting_demo.html")
    return f"file://{html_path}"

def main():
    
    path=get_html_path() # 取得當前資料夾底下html檔案的絕對路徑

    with sync_playwright() as p:
        # 啟動瀏覽器
        browser = p.chromium.launch(headless=False,slow_mo=500)

        #開啟新頁面
        page=browser.new_page()

        #訪問頁面
        page.goto(path)

        # 等待3秒以觀察效果
        page.wait_for_timeout(3000)

        browser.close()


if __name__ == "__main__":
    main()