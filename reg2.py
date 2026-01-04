import random
import time
import re
import requests
import logging
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- CẤU HÌNH GLOBAL ---
# Cài đặt Driver 1 lần duy nhất để tránh lỗi "Text file busy"
try:
    DRIVER_PATH = ChromeDriverManager().install()
except Exception as e:
    print(f"Lỗi cài đặt Driver ban đầu: {e}")
    DRIVER_PATH = None

def get_chrome_options(thread_id):
    """Cấu hình Chrome tối ưu cho Cloud Shell và Reg Clone"""
    chrome_options = Options()
    
    # --- CẤU HÌNH QUAN TRỌNG CHO CLOUD SHELL/LINUX ---
    chrome_options.add_argument("--headless=new") # Chạy ẩn không cần màn hình
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # --- CẤU HÌNH FAKE USER (ANTIDETECT) ---
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
    ]
    user_agent = random.choice(user_agents)
    chrome_options.add_argument(f"user-agent={user_agent}")
    
    # Các flag ẩn danh tính automation
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    
    # Vị trí cửa sổ ảo (dù headless nhưng vẫn set để tránh nghi ngờ)
    x_pos = thread_id * 320
    chrome_options.add_argument(f"--window-size=375,812") # Kích thước mobile
    chrome_options.add_argument(f"--window-position={x_pos},0")
    
    return chrome_options

def checkuid(cookie_string):
    """Lấy UID từ Cookie"""
    try:
        headers = {
            'authority': 'www.facebook.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'vi-VN,vi;q=0.9',
            'dpr': '1',
            'sec-ch-prefers-color-scheme': 'light',
            'sec-ch-ua-mobile': '?0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'cookie': cookie_string,
        }
        
        # Thử lấy từ trang mobile basic hoặc confirm email
        response = requests.get('https://mbasic.facebook.com/profile.php', headers=headers).text
        
        # Pattern tìm c_user (chính xác nhất)
        if "c_user=" in cookie_string:
            match = re.search(r'c_user=(\d+)', cookie_string)
            if match:
                return match.group(1)

        # Fallback: Tìm trong source HTML
        pattern = r'"ACCOUNT_ID":\s*"(.*?)"'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
            
        # Fallback 2: Tìm target_id trong link
        match = re.search(r'target_id=(\d+)', response)
        if match:
            return match.group(1)

        return 0
    except Exception as e:
        print(f"Lỗi check UID: {e}")
        return 0

def run_registration(args):
    thread_id, num_accounts = args
    if not DRIVER_PATH:
        print(f"Luồng {thread_id}: Không tìm thấy Driver Path. Dừng.")
        return

    for i in range(num_accounts):
        driver = None
        try:
            print(f"Luồng {thread_id}: Bắt đầu reg acc thứ {i+1}...")
            
            # Khởi tạo Service với đường dẫn Driver đã cài sẵn
            service = Service(executable_path=DRIVER_PATH)
            options = get_chrome_options(thread_id)
            
            driver = webdriver.Chrome(service=service, options=options)
            
            # Bypass detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # --- QUY TRÌNH REG ---
            ho_list = ["Nguyễn", "Trần", "Lê", "Phạm", "Huỳnh", "Hoàng", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
            ten_list = ["Nam", "Long", "Huy", "Tuấn", "Khoa", "Tài", "Duy", "Sơn", "Phúc", "Trí", "Linh", "Trang", "Lan", "Hương", "Nhung", "Mai", "Yến", "Thảo", "Vy", "Ngân"]
            ho = random.choice(ho_list)
            ten = random.choice(ten_list)

            # Vào trang reg mobile
            driver.get("https://m.facebook.com/reg/")
            time.sleep(random.uniform(2, 4))

            # Điền Họ Tên
            try:
                # Đôi khi FB hiện form nối liền hoặc tách rời, dùng wait để chắc chắn
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, 'lastname'))).send_keys(ten)
                driver.find_element(By.NAME, 'firstname').send_keys(ho)
            except:
                # Trường hợp layout khác
                driver.refresh()
                time.sleep(2)
                driver.find_element(By.NAME, 'lastname').send_keys(ten)
                driver.find_element(By.NAME, 'firstname').send_keys(ho)
            
            time.sleep(1)

            # Điền ngày tháng năm sinh
            try:
                # Tìm nút Next/Submit để focus, tránh lỗi che khuất
                driver.execute_script("window.scrollTo(0, 200)") 
                
                select_day = Select(driver.find_element(By.ID, "day"))
                random_day = random.choice([opt.get_attribute("value") for opt in select_day.options if opt.get_attribute("value") != "0"])
                select_day.select_by_value(random_day)

                select_month = Select(driver.find_element(By.ID, "month"))
                random_month = random.choice([opt.get_attribute("value") for opt in select_month.options if opt.get_attribute("value") != "0"])
                select_month.select_by_value(random_month)

                select_year = Select(driver.find_element(By.ID, "year"))
                random_year = str(random.randint(1990, 2005))
                select_year.select_by_value(random_year)
            except Exception as e:
                print(f"Luồng {thread_id}: Lỗi điền ngày sinh: {e}")

            # Điền SĐT (Fake)
            # Tạo đầu số ngẫu nhiên đa dạng hơn để tránh spam
            prefixes = ['090', '093', '097', '098', '091', '094', '086', '088']
            random_number = random.choice(prefixes) + str(random.randint(1000000, 9999999))
            passss = 'Huydeptrai123@@' # Nên đổi pass này ngẫu nhiên hơn nếu reg SLL
            
            try:
                driver.find_element(By.NAME, 'reg_email__').send_keys(random_number)
            except:
                # Form dạng wizard (từng bước)
                pass 
                
            # Giới tính
            try:
                sex_val = random.choice(["1", "2"])
                # Dùng JS click cho chắc chắn nếu bị overlay
                sex_radio = driver.find_element(By.CSS_SELECTOR, f"input[name='sex'][value='{sex_val}']")
                driver.execute_script("arguments[0].click();", sex_radio)
            except:
                pass

            # Password
            try:
                driver.find_element(By.NAME, 'reg_passwd__').send_keys(passss)
            except:
                pass

            # Nút Submit (Đăng ký)
            time.sleep(1)
            try:
                submit_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.NAME, 'websubmit'))
                )
                submit_btn.click()
                print(f"Luồng {thread_id}: Đã bấm đăng ký...")
            except Exception as e:
                print(f"Luồng {thread_id}: Lỗi nút submit: {e}")

            # --- CHỜ KẾT QUẢ ---
            # Logic: Chờ trang chuyển hướng hoặc xuất hiện element nhập code
            # Nếu vào được trang nhập code -> Coi như Live bước 1 -> Lấy Cookie
            try:
                WebDriverWait(driver, 30).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.NAME, 'c')), # Ô nhập code thường tên là 'c' hoặc 'n'
                        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'code')]")),
                        EC.url_contains("confirmemail"),
                        EC.url_contains("checkpoint")
                    )
                )
                print(f"Luồng {thread_id}: Phát hiện chuyển hướng thành công.")
            except:
                print(f"Luồng {thread_id}: Time out chờ phản hồi (có thể mạng lag hoặc bị chặn).")

            # Lấy Cookie và Check
            cookies = driver.get_cookies()
            cookie_string = "; ".join(f"{cookie['name']}={cookie['value']}" for cookie in cookies) + ";"
            
            # Nếu có c_user trong cookie là ngon nhất
            if "c_user" in cookie_string:
                uid = re.search(r'c_user=(\d+)', cookie_string).group(1)
                print(f"Luồng {thread_id}: SUCCESS! UID: {uid}")
            else:
                # Check server
                uid = checkuid(cookie_string)

            if uid and str(uid) != "0":
                with open('TK.txt', "a", encoding="utf-8") as f:
                    # Format: UID|User|Pass|Cookie
                    f.write(f"{uid}|{random_number}|{passss}|{cookie_string}\n")
                print(f"Luồng {thread_id}: -> Ghi file thành công.")
            else:
                print(f"Luồng {thread_id}: Reg thất bại hoặc dính checkpoint ngay lập tức.")

        except Exception as e:
            print(f"Luồng {thread_id}: Lỗi ngoại lệ - {e}")
        finally:
            if driver:
                driver.quit()

def extract_uids():
    try:
        with open('TK.txt', 'r', encoding="utf-8") as tk_file:
            lines = tk_file.readlines()
        
        uids = []
        for line in lines:
            parts = line.split('|')
            if len(parts) > 0 and parts[0].strip().isdigit():
                uids.append(parts[0].strip())
                
        with open('uid.txt', 'w', encoding="utf-8") as uid_file:
            for uid in uids:
                uid_file.write(f"{uid}\n")
        print(f"Đã tách {len(uids)} UID vào uid.txt")
    except FileNotFoundError:
        print("Chưa có file TK.txt")
    except Exception as e:
        print(f"Lỗi khi tách UID: {e}")

def main():
    print("--- TOOL REG FACEBOOK NO VERIFY (TEST EDU) ---")
    try:
        choice = int(input('Chọn chức năng (1: Chạy đăng ký, 2: Tách UID): '))
    except:
        choice = 0

    if choice == 1:
        try:
            num_threads = int(input('SỐ LUỒNG (Khuyên dùng 1-5 trên CloudShell): '))
            total_accounts = int(input('TỔNG SỐ ACC MUỐN REG: '))
            
            if num_threads < 1: num_threads = 1
            
            # Chia việc cho các luồng
            accounts_per_thread = total_accounts // num_threads
            remainder = total_accounts % num_threads
            
            args_list = []
            for i in range(num_threads):
                count = accounts_per_thread + (1 if i < remainder else 0)
                if count > 0:
                    args_list.append((i, count))

            print(f"Bắt đầu chạy {num_threads} luồng...")
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                executor.map(run_registration, args_list)
                
        except ValueError:
            print("Vui lòng nhập số hợp lệ.")
            
    elif choice == 2:
        extract_uids()
    else:
        print("Lựa chọn không hợp lệ")

if __name__ == "__main__":
    main()
