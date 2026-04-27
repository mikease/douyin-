import time
import requests
import re
from playwright.sync_api import sync_playwright

# --- 配置区 ---
PUSHPLUS_TOKEN = '你的TOKEN' 

def send_pushplus(title, data_list, start_time, end_time):
    print("\n" + "═"*60)
    print(f"📊 {title}")
    print(f"⏰ 运行周期: {start_time} - {end_time}")
    print("-" * 60)
    print(f"{'好友昵称':<15} | {'状态':<12} | {'火花详情':<10}")
    print("-" * 60)
    for i in data_list:
        print(f"{i['name']:<15} | {i['status']:<12} | {i['days']:<10}")
    print("═"*60 + "\n")

    if not PUSHPLUS_TOKEN or PUSHPLUS_TOKEN == '你的TOKEN': return
    
    rows = ""
    for i in data_list:
        status_color = "#4CAF50" if "已续火" in i['status'] else "#FF9800"
        rows += f"""
        <tr style="border-bottom: 1px solid #eee;">
            <td style="padding: 10px;">{i['name']}</td>
            <td style="padding: 10px;"><span style="background: {status_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{i['status']}</span></td>
            <td style="padding: 10px;">{i['days']}</td>
        </tr>"""

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 500px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
        <div style="background: #fe2c55; color: white; padding: 15px; text-align: center; font-size: 18px; font-weight: bold;">
            抖音火花全量监控报告
        </div>
        <div style="padding: 10px; font-size: 13px; color: #666; background: #fafafa;">
            ⏱ 运行周期：{start_time} - {end_time}
        </div>
        <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 14px;">
            <tr style="background: #f8f8f8; font-weight: bold;">
                <td style="padding: 10px;">好友</td>
                <td style="padding: 10px;">状态</td>
                <td style="padding: 10px;">详情</td>
            </tr>
            {rows}
        </table>
    </div>
    """
    try:
        requests.post('http://www.pushplus.plus/send', json={"token": PUSHPLUS_TOKEN, "title": title, "content": html_content, "template": "html"}, timeout=5)
    except: pass

def fire_mission_v32_stable():
    FIRE_EMOJI = "[赞]"
    all_fire_data = [] 
    processed_names = set() 
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()
        
        print(f"🚀 启动自动续火稳健版...")
        page.goto("https://www.douyin.com/", wait_until="domcontentloaded")
        
        try:
            page.locator('p:has-text("私信"), span:has-text("私信")').first.click()
            page.wait_for_selector('div[class*="FYm03pQm"]', timeout=15000)
        except:
            page.locator('p:has-text("私信"), span:has-text("私信")').first.click(force=True)

        time.sleep(3) # 给列表多一点加载时间
        start_time = time.strftime("%H:%M:%S")

        while True:
            items = page.locator('div[class*="FYm03pQm"]').all()
            for item in items:
                try:
                    name_el = item.locator('.FUWX84Hq').first
                    if not name_el.is_visible(): continue
                    name = name_el.inner_text().strip()
                    if name in processed_names: continue

                    icon = item.locator('img[src*="chat_days"]').first
                    if not icon.is_visible(): continue
                    
                    src = icon.get_attribute("src") or ""
                    is_disable = "chat_days_disable" in src
                    
                    # 抓取数据
                    display_val = ""
                    days_el = item.locator('.zjaP1Ag7').first 
                    if days_el.is_visible():
                        raw_val = days_el.inner_text().strip()
                        display_val = f"{raw_val}天" if raw_val.isdigit() else raw_val
                    else:
                        clean_text = re.sub(r'\d{1,2}:\d{2}', '', item.inner_text())
                        nums = re.findall(r'\d+', clean_text)
                        display_val = f"{max(nums, key=int)}天" if nums else "新火花"

                    if not is_disable:
                        all_fire_data.append({"name": name, "days": display_val, "status": "已续火 ✅"})
                        processed_names.add(name)
                    else:
                        item.click(force=True)
                        time.sleep(1.5) # 增加切换窗口等待
                        
                        last_chat = page.locator('div[class*="chat-item-text"]').last
                        if last_chat.is_visible() and FIRE_EMOJI in last_chat.inner_text():
                            all_fire_data.append({"name": name, "days": display_val, "status": "已续火 ✅"})
                        else:
                            editor = page.locator('div[contenteditable="true"]').first
                            if editor.is_visible():
                                editor.fill(FIRE_EMOJI)
                                time.sleep(0.5) # 填入表情后顿一下
                                page.keyboard.press("Enter")
                                # --- 核心改动：等待消息物理发出 ---
                                time.sleep(1.5) 
                                all_fire_data.append({"name": name, "days": display_val, "status": "今日续火 🔥"})
                                print(f"✅ {name} 续火完成")

                        processed_names.add(name)
                        close_btn = page.locator('span.n9QukYLz:has-text("关闭会话")').first
                        if close_btn.is_visible(): 
                            close_btn.click(force=True)
                        time.sleep(0.8) # 慢下来，稳就是快
                except: continue

            at_bottom = page.evaluate("""() => {
                const el = document.querySelector('div[class*="FYm03pQm"]')?.parentElement;
                if (!el) return true;
                const prev = el.scrollTop;
                el.scrollBy(0, 850);
                return Math.abs(el.scrollTop - prev) < 5;
            }""")
            time.sleep(1.5) # 滚动后的缓冲
            if at_bottom: break

        end_time = time.strftime("%H:%M:%S")
        all_fire_data.sort(key=lambda x: "今日续火" not in x['status'])
        send_pushplus(f"火花日报 (共{len(all_fire_data)}人)", all_fire_data, start_time, end_time)
        browser.close()

if __name__ == "__main__":
    fire_mission_v32_stable()
