from playwright.sync_api import sync_playwright

def main():
    
    path="https://www.thsrc.com.tw/" # 網址

    with sync_playwright() as p:
        # 啟動瀏覽器
        browser = p.chromium.launch(headless=False,slow_mo=500)

        # 開啟新頁面
        page=browser.new_page()

        # 訪問頁面
        page.goto(path)

        # 等待DOM結構已解析完成
        page.wait_for_load_state("domcontentloaded")

        # 取得並點擊按鈕觸發異步操作
        page.locator("button",has_text="我同意").click()  

        lis = page.locator("ul#alltype-news.news-list > li").all()
        print(type(lis))
        print(f"共找到 {len(lis)} 筆最新消息")
        for item in lis:
            date = item.locator("div.news-date").text_content()
            title = item.locator("div.news-title").text_content()
            print(date)
            print(title)
            print("=" * 60)

        # 等待3秒以觀察效果
        page.wait_for_timeout(3000)

        # 關閉瀏覽器
        browser.close()


if __name__ == "__main__":
    main()