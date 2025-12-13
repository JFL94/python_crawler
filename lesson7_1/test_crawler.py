"""
爬蟲功能測試腳本
"""
import asyncio
from crawler import fetch_exchange_rates, clean_exchange_data

async def test_crawler():
    print("開始爬蟲測試...")
    print("-" * 50)
    
    try:
        # 測試爬蟲
        print("🕷️  正在爬取匯率資料...")
        raw_data = await fetch_exchange_rates()
        
        print(f"\n✅ 爬蟲成功！")
        print(f"原始資料結構: {raw_data}")
        
        # 測試資料清理
        print("\n🔄 清理資料...")
        cleaned_data = clean_exchange_data(raw_data)
        
        print(f"✅ 清理完成！")
        print(f"有效幣別數: {len(cleaned_data)}")
        
        if cleaned_data:
            print("\n前 5 筆資料:")
            for i, item in enumerate(cleaned_data[:5], 1):
                print(f"  {i}. {item['幣別']}: 買入={item['本行即期買入']}, 賣出={item['本行即期賣出']}")
        else:
            print("⚠️  沒有提取到有效的匯率資料")
            
    except Exception as e:
        print(f"❌ 爬蟲測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_crawler())
