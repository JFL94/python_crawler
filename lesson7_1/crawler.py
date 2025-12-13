"""
匯率爬蟲模組
使用 crawl4ai 爬取臺灣銀行牌告匯率
"""

import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy


async def fetch_exchange_rates() -> dict:
    """
    爬取匯率資料
    
    Returns:
        dict: 包含匯率資料的字典
    """
    schema = {
        "name": "匯率資訊",
        "baseSelector": "table[title='牌告匯率'] tr",
        "fields": [
            {
                "name": "幣別",
                "selector": "td[data-table='幣別'] div.print_show",
                "type": "text"
            },
            {
                "name": "本行即期買入",
                "selector": "td[data-table='本行即期買入']",
                "type": "text"
            },
            {
                "name": "本行即期賣出",
                "selector": "td[data-table='本行即期賣出']",
                "type": "text"
            }
        ]
    }

    strategy = JsonCssExtractionStrategy(schema)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=strategy
    )

    async with AsyncWebCrawler() as crawler:
        url = 'https://rate.bot.com.tw/xrt?Lang=zh-TW'
        result = await crawler.arun(url=url, config=run_config)
        
        if result.extracted_content:
            data = json.loads(result.extracted_content)
            return data
        else:
            return {"匯率資訊": []}


def clean_exchange_data(raw_data: dict) -> list:
    """清理並驗證匯率資料，篩選出有效的交易幣別"""
    cleaned_rates = []
    
    if "匯率資訊" not in raw_data:
        return cleaned_rates
    
    for item in raw_data.get("匯率資訊", []):
        currency = item.get("幣別", "").strip()
        buy_rate = item.get("本行即期買入", "").strip()
        sell_rate = item.get("本行即期賣出", "").strip()
        
        if currency and buy_rate and sell_rate:
            try:
                buy_float = float(buy_rate)
                sell_float = float(sell_rate)
                
                if buy_float > 0 and sell_float > 0:
                    cleaned_rates.append({
                        "幣別": currency,
                        "本行即期買入": buy_float,
                        "本行即期賣出": sell_float
                    })
            except ValueError:
                continue
    
    return cleaned_rates


def convert_currency(twd_amount: float, exchange_rate: float) -> float:
    """計算台幣轉換為外幣"""
    if exchange_rate <= 0 or twd_amount < 0:
        return 0.0
    return round(twd_amount / exchange_rate, 2)
