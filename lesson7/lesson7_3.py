import asyncio,json
from crawl4ai import AsyncWebCrawler,CrawlerRunConfig,CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    # 模擬產品網頁
    html = """
        <html>
            <body>
                <div class='product-card'>
                    <h2>電競筆電 - 高效能遊戲機</h2>
                    <p>這款筆電配備最新的 RTX 4070 顯示卡，
                        搭配 Intel i9 處理器，適合專業遊戲玩家。</p>
                    <div class='price-section'>
                        <span class='old-price'>原價 $1499.99</span>
                    <span class='new-price'>特價 $1299.99</span>
                    </div>
                    <a href='https://example.com/gaming-laptop'>查看詳情</a>
                </div>
                <div class='product-card'>
                    <h2>無線滑鼠 - 人體工學設計</h2>
                    <p>符合人體工學的無線滑鼠，電池續航力長達 3 個月。</p>
                    <div class='price-section'>
                        <span class='new-price'>$29.99</span>
                    </div>
                    <a href='https://example.com/wireless-mouse'>查看詳情</a>
                </div>
            </body>
        </html> 
    """

    schema ={
        "name":"項目名稱",
        "baseSelector":"div.product-card",
        "fields":[
            {
                "name":"產品名稱",
                "selector":"h2",
                "type":"text"
            },
            {
                "name":"產品介紹",
                "selector":"p",
                "type":"text"
            },
            {
                "name":"原價",
                "selector":".price-section span.old-price",
                "type":"text",
                "default": ""
            },
            {
                "name":"特價",
                "selector":".price-section span.new-price",
                "type":"text"
            },
            {
                "name":"詳情連結",
                "selector":"a",
                "type":"attribute",
                "attribute":"href"
            }
        ]
    }

    strategy = JsonCssExtractionStrategy(schema)

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=strategy
        )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=f"raw://{html}",
            config=run_config)
        data = json.loads(result.extracted_content)
        for item in data:
            print(f"產品名稱: {item['產品名稱']}")
            print(f"產品介紹: {item['產品介紹']}")
            print(f"原價: {item['原價']}")
            print(f"特價: {item['特價']}")
            print(f"查看詳情: {item['詳情連結']}")
            print("=============")

        # for item in data:
        #     print(f"產品名稱: {item.get('產品名稱','無')}")
        #     print(f"產品介紹: {item.get('產品介紹','無')}")
        #     print(f"原價: {item.get('原價','無')}")
        #     print(f"特價: {item.get('特價','無')}")
        #     print(f"查看詳情: {item.get('詳情連結','無')}")
        #     print("=============")

if __name__ == "__main__":
    asyncio.run(main())