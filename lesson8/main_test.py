"""
台灣銀行匯率查詢系統 - tkinter 桌面應用程式

整合 crawl4ai 爬蟲與 tkinter GUI，提供即時匯率查詢與台幣轉換計算功能。
"""

import asyncio
import json
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
from datetime import datetime
from typing import Optional, List, Dict

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy


# ============= 爬蟲模組 =============

async def fetch_exchange_rates() -> Optional[List[Dict[str, str]]]:
    """
    爬取台灣銀行匯率資訊
    
    使用 JsonCssExtractionStrategy 結構化提取，返回清理後的資料。
    
    Returns:
        List[Dict[str, str]]: 匯率資料清單，每個元素包含：
            - 幣別 (currency)
            - 本行即期買入 (buy_rate)
            - 本行即期賣出 (sell_rate)
        None: 若爬蟲失敗
    """
    try:
        # 定義提取結構
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
            data = json.loads(result.extracted_content)
            
            # 資料清理與驗證
            cleaned_data = []
            for item in data:
                currency = item.get("幣別", "").strip()
                buy = item.get("本行即期買入", "").strip()
                sell = item.get("本行即期賣出", "").strip()
                
                if currency:  # 只保留有貨幣名稱的資料
                    cleaned_data.append({
                        "幣別": currency,
                        "本行即期買入": buy if buy else "暫停交易",
                        "本行即期賣出": sell if sell else "暫停交易"
                    })
            
            return cleaned_data
            
    except Exception as e:
        print(f"爬蟲錯誤: {e}")
        return None


# ============= GUI 應用程式 =============

class ExchangeRateApp(tk.Tk):
    """匯率查詢應用程式主視窗"""
    
    def __init__(self):
        """初始化應用程式"""
        super().__init__()
        
        # 視窗屬性
        self.title("🏦 台灣銀行匯率查詢系統")
        self.geometry("1200x750")
        self.config(bg="#f0f0f0")
        
        # 應用程式狀態
        self.exchange_data: Optional[List[Dict[str, str]]] = None
        self.last_update: Optional[datetime] = None
        self.is_loading = False
        
        # 建立 UI
        self._setup_ui()
        
        # 載入初始資料
        self._load_initial_data()
    
    def _setup_ui(self):
        """建立 UI 元件"""
        # ===== 標題欄 =====
        header_frame = tk.Frame(self, bg="white", relief=tk.RAISED, bd=1)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        
        header_content = tk.Frame(header_frame, bg="white")
        header_content.pack(fill=tk.X, padx=15, pady=15)
        
        # 標題
        title_label = tk.Label(
            header_content,
            text="🏦 台灣銀行匯率查詢系統",
            font=("Arial", 24, "bold"),
            bg="white",
            fg="#2c3e50"
        )
        title_label.pack(side=tk.LEFT, padx=0)
        
        # 更新按鈕
        self.update_btn = tk.Button(
            header_content,
            text="🔄 更新匯率",
            font=("Arial", 16, "bold"),
            bg="#3498db",
            fg="white",
            padx=15,
            pady=10,
            command=self._fetch_data_thread,
            relief=tk.RAISED,
            bd=2
        )
        self.update_btn.pack(side=tk.LEFT, padx=15)
        
        # 狀態標籤
        self.status_label = tk.Label(
            header_content,
            text="",
            font=("Arial", 14),
            bg="white",
            fg="#3498db"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # 時間標籤
        self.time_label = tk.Label(
            header_content,
            text="",
            font=("Arial", 14),
            bg="white",
            fg="#7f8c8d"
        )
        self.time_label.pack(side=tk.RIGHT, padx=0)
        
        # ===== 主容器 =====
        main_container = tk.Frame(self, bg="#f0f0f0")
        main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # 左側框架 - 匯率表格
        left_frame = tk.LabelFrame(
            main_container,
            text="📊 匯率資訊",
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#2c3e50",
            padx=15,
            pady=15
        )
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        
        # Treeview + 捲軸
        tree_scroll = ttk.Scrollbar(left_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(
            left_frame,
            columns=("買入", "賣出"),
            height=15,
            yscrollcommand=tree_scroll.set,
            show="tree headings"
        )
        tree_scroll.config(command=self.tree.yview)
        
        # Treeview 欄位設定
        self.tree.column("#0", width=200, anchor=tk.CENTER)
        self.tree.column("買入", width=160, anchor=tk.CENTER)
        self.tree.column("賣出", width=160, anchor=tk.CENTER)
        
        self.tree.heading("#0", text="幣別")
        self.tree.heading("買入", text="本行即期買入")
        self.tree.heading("賣出", text="本行即期賣出")
        
        # 設定字體大小
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 16, "bold"))
        style.configure("Treeview", font=("Arial", 14), rowheight=35)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 右側框架 - 台幣轉換計算器
        right_frame = tk.LabelFrame(
            main_container,
            text="💱 台幣轉換計算器",
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#2c3e50",
            padx=20,
            pady=20
        )
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=4)
        
        # 台幣金額輸入
        twd_label = tk.Label(
            right_frame,
            text="💵 台幣金額",
            font=("Arial", 16),
            bg="white",
            fg="#2c3e50"
        )
        twd_label.pack(anchor=tk.W, pady=10)
        
        self.twd_entry = tk.Entry(
            right_frame,
            font=("Arial", 16),
            width=25,
            relief=tk.SUNKEN,
            bd=2
        )
        self.twd_entry.pack(anchor=tk.W, pady=10)
        self.twd_entry.insert(0, "1000")
        
        # 目標貨幣選擇
        currency_label = tk.Label(
            right_frame,
            text="🌍 目標貨幣",
            font=("Arial", 16),
            bg="white",
            fg="#2c3e50"
        )
        currency_label.pack(anchor=tk.W, pady=10)
        
        self.currency_combo = ttk.Combobox(
            right_frame,
            font=("Arial", 16),
            state="readonly",
            width=23
        )
        self.currency_combo.pack(anchor=tk.W, pady=10)
        
        # 計算按鈕
        calculate_btn = tk.Button(
            right_frame,
            text="💱 計算轉換",
            font=("Arial", 16, "bold"),
            bg="#27ae60",
            fg="white",
            padx=20,
            ipady=5,
            command=self._calculate_conversion,
            relief=tk.RAISED,
            bd=2
        )
        calculate_btn.pack(anchor=tk.W, pady=25)
        
        # 結果顯示
        result_label = tk.Label(
            right_frame,
            text="📊 轉換結果",
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#2c3e50"
        )
        result_label.pack(anchor=tk.W, pady=10)
        
        self.result_text = tk.Text(
            right_frame,
            font=("Arial", 14),
            height=10,
            width=30,
            relief=tk.SUNKEN,
            bd=2,
            bg="#ecf0f1",
            fg="#2c3e50",
            state=tk.DISABLED
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=15)
        
        # 說明文字
        info_label = tk.Label(
            right_frame,
            text="💡 買入：您賣台幣給銀行\n💡 賣出：您向銀行買外幣",
            font=("Arial", 12),
            bg="white",
            fg="#7f8c8d",
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W, pady=5)
    
    def _load_initial_data(self):
        """載入初始資料"""
        self._fetch_data_thread()
    
    def _fetch_data_thread(self):
        """在背景執行緒中爬取資料"""
        if self.is_loading:
            return
        
        self.is_loading = True
        self._show_loading()
        
        def run_async():
            """在新的事件迴圈中執行非同步函數"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                data = loop.run_until_complete(fetch_exchange_rates())
                # 使用 after 確保在主執行緒中更新 UI
                self.after(0, lambda: self._update_ui_with_data(data))
            except Exception as e:
                self.after(0, lambda: self._show_error(f"爬蟲失敗: {str(e)}"))
            finally:
                loop.close()
                self.is_loading = False
        
        # 啟動背景執行緒
        thread = Thread(target=run_async, daemon=True)
        thread.start()
    
    def _show_loading(self):
        """顯示載入狀態"""
        self.status_label.config(text="⏳ 載入中...", foreground="#3498db")
        self.update_btn.config(state="disabled")
        self.config(cursor="watch")
    
    def _hide_loading(self):
        """隱藏載入狀態"""
        self.config(cursor="")
        self.update_btn.config(state="normal")
    
    def _update_ui_with_data(self, data: Optional[List[Dict[str, str]]]):
        """更新 UI 資料"""
        self._hide_loading()
        
        if data is None or len(data) == 0:
            messagebox.showerror("錯誤", "無法取得匯率資料")
            self.status_label.config(text="❌ 更新失敗", foreground="#e74c3c")
            return
        
        # 儲存資料
        self.exchange_data = data
        self.last_update = datetime.now()
        
        # 更新表格
        self._update_treeview()
        
        # 更新下拉選單
        self._update_currency_combo()
        
        # 更新時間標籤
        self.time_label.config(
            text=f"最後更新: {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # 顯示成功訊息（3秒後消失）
        self.status_label.config(text="✅ 更新成功", foreground="#27ae60")
        self.after(3000, lambda: self.status_label.config(text=""))
    
    def _update_treeview(self):
        """更新 Treeview 資料"""
        # 清空舊資料
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 插入新資料
        if self.exchange_data:
            for idx, item in enumerate(self.exchange_data):
                currency = item.get("幣別", "")
                buy = item.get("本行即期買入", "暫停交易")
                sell = item.get("本行即期賣出", "暫停交易")
                
                # 設定行的背景色（交替顏色）
                tag = "oddrow" if idx % 2 == 0 else "evenrow"
                self.tree.insert("", "end", text=currency, values=(buy, sell), tags=(tag,))
            
            # 配置標籤樣式
            self.tree.tag_configure("oddrow", background="#ecf0f1")
            self.tree.tag_configure("evenrow", background="white")
    
    def _update_currency_combo(self):
        """更新貨幣下拉選單（只顯示可交易的貨幣）"""
        available_currencies = []
        
        if self.exchange_data:
            for item in self.exchange_data:
                currency = item.get("幣別", "").strip()
                buy = item.get("本行即期買入", "").strip()
                sell = item.get("本行即期賣出", "").strip()
                
                # 只加入可交易的貨幣（買入和賣出都有值）
                if currency and buy and buy != "暫停交易" and sell and sell != "暫停交易":
                    available_currencies.append(currency)
        
        self.currency_combo['values'] = available_currencies
        if available_currencies:
            self.currency_combo.current(0)
    
    def _find_rate_by_currency(self, currency: str) -> Optional[Dict[str, str]]:
        """根據貨幣代碼找到匯率資料"""
        if not self.exchange_data:
            return None
        
        for item in self.exchange_data:
            if item.get("幣別") == currency:
                return item
        
        return None
    
    def _calculate_conversion(self):
        """計算台幣轉換"""
        try:
            # 驗證輸入
            twd_amount_str = self.twd_entry.get().strip()
            if not twd_amount_str:
                messagebox.showwarning("警告", "請輸入台幣金額")
                return
            
            twd_amount = float(twd_amount_str)
            if twd_amount <= 0:
                messagebox.showwarning("警告", "金額必須大於 0")
                return
            
            # 驗證選擇
            selected_currency = self.currency_combo.get()
            if not selected_currency:
                messagebox.showwarning("警告", "請選擇目標貨幣")
                return
            
            # 查找匯率
            rate_data = self._find_rate_by_currency(selected_currency)
            if not rate_data:
                messagebox.showerror("錯誤", "找不到該貨幣的匯率")
                return
            
            try:
                buy_rate = float(rate_data["本行即期買入"])
                sell_rate = float(rate_data["本行即期賣出"])
            except ValueError:
                messagebox.showerror("錯誤", "匯率資料格式錯誤")
                return
            
            # 計算
            buy_result = twd_amount / buy_rate
            sell_result = twd_amount / sell_rate
            
            # 格式化結果
            result_text = f"""
═══════════════════════════
💰 轉換金額: {twd_amount:,.2f} 台幣
🌍 目標貨幣: {selected_currency}
═══════════════════════════

📤 您賣台幣給銀行 (買入匯率)
   匯率: {buy_rate}
   可得: {buy_result:.2f} {selected_currency}

📥 您向銀行買外幣 (賣出匯率)
   匯率: {sell_rate}
   需付: {sell_result:.2f} {selected_currency}

═══════════════════════════
計算時間: {datetime.now().strftime('%H:%M:%S')}
"""
            
            # 顯示結果
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", result_text)
            self.result_text.config(state=tk.DISABLED)
            
        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的金額數字")
        except Exception as e:
            messagebox.showerror("錯誤", f"計算失敗: {str(e)}")
    
    def _show_error(self, message: str):
        """顯示錯誤訊息"""
        self._hide_loading()
        self.status_label.config(text="❌ 載入失敗", foreground="#e74c3c")
        messagebox.showerror("錯誤", message)


# ============= 主程式入口 =============

def main():
    """應用程式入口"""
    app = ExchangeRateApp()
    app.mainloop()


if __name__ == "__main__":
    main()
