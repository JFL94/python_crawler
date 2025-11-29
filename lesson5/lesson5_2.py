from playwright.sync_api import sync_playwright

def main():
    
    path="https://www.thsrc.com.tw/" # 取得當前資料夾底下html檔案的絕對路徑

    with sync_playwright() as p:
        # 啟動瀏覽器
        browser = p.chromium.launch(headless=False,slow_mo=500)

        # 開啟新頁面
        page=browser.new_page()

        # 訪問頁面
        page.goto(path)

        # 等待DOM結構已解析完成
        page.wait_for_load_state("domcontentloaded")

        # 等待3秒以觀察效果
        page.wait_for_timeout(3000)

        # 關閉瀏覽器
        browser.close()


if __name__ == "__main__":
    main()