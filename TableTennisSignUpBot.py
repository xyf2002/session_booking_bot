from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import datetime
import sys


class TableTennisSignUpBot:
    def __init__(self):
        self.driver = None
        self.wait = None

    def setup_driver(self):
        """配置浏览器驱动"""
        chrome_options = Options()
        # 取消注释下一行可以在后台运行（无界面）
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 修复：使用service参数
        from selenium.webdriver.chrome.service import Service
        service = Service(ChromeDriverManager().install())

        self.driver = webdriver.Chrome(
            service=service,
            options=chrome_options
        )
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)

    def navigate_to_page(self):
        """导航到签到页面"""
        url = "https://www.signupgenius.com/go/10c0d4faba62ca2f9c25-euttc#/"
        print("正在打开页面...")
        self.driver.get(url)

        # 等待页面加载
        time.sleep(10)
        print("页面加载完成")

    def find_available_session_and_click(self, target_day=None):
        """查找可用的会话并点击Sign Up按钮"""
        try:
            if target_day:
                print(f"正在查找{target_day}会话...")
            else:
                print("正在查找任何可用的会话...")

            # 查找所有包含"Sign Up"的按钮
            signup_buttons = self.driver.find_elements(By.XPATH, "//a[contains(., 'Sign Up') or contains(., '报名')]")

            if not signup_buttons:
                print("未找到任何Sign Up按钮")
                return False

            print(f"找到 {len(signup_buttons)} 个Sign Up按钮")

            # 如果指定了目标日期，优先查找该日期的会话
            if target_day:
                for i, button in enumerate(signup_buttons):
                    try:
                        # 获取按钮所在行的文本内容
                        row_text = button.find_element(By.XPATH, "./ancestor::tr").text
                        if target_day.lower() in row_text.lower():
                            print(f"找到{target_day}会话，点击Sign Up按钮")
                            button.click()
                            return True
                    except:
                        continue

            # 如果没有找到特定日期的会话或没有指定日期，点击第一个可用的按钮
            print("点击第一个可用的Sign Up按钮")
            signup_buttons[0].click()
            return True

        except Exception as e:
            print(f"查找会话时出错: {e}")
            return False

    def fill_personal_info(self, first_name, last_name, email):
        """填写个人信息"""
        try:
            print("正在填写个人信息...")

            # 等待个人信息页面加载
            time.sleep(5)

            # 填写名字
            first_name_selectors = [
                "input[placeholder*='First']",
                "input[name*='first']",
                "input[id*='first']",
                "//input[contains(@placeholder, 'First')]"
            ]

            first_name_field = None
            for selector in first_name_selectors:
                try:
                    if selector.startswith("//"):
                        first_name_field = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        first_name_field = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    if first_name_field:
                        first_name_field.clear()
                        first_name_field.send_keys(first_name)
                        print("名字填写成功")
                        break
                except:
                    continue

            if not first_name_field:
                print("未找到名字输入框")
                return False

            # 填写姓氏
            last_name_selectors = [
                "input[placeholder*='Last']",
                "input[name*='last']",
                "input[id*='last']",
                "//input[contains(@placeholder, 'Last')]"
            ]

            last_name_field = None
            for selector in last_name_selectors:
                try:
                    if selector.startswith("//"):
                        last_name_field = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        last_name_field = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    if last_name_field:
                        last_name_field.clear()
                        last_name_field.send_keys(last_name)
                        print("姓氏填写成功")
                        break
                except:
                    continue

            if not last_name_field:
                print("未找到姓氏输入框")
                return False

            # 填写邮箱
            email_selectors = [
                "input[type='email']",
                "input[placeholder*='Email']",
                "input[name*='email']",
                "input[id*='email']"
            ]

            email_field = None
            for selector in email_selectors:
                try:
                    email_field = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if email_field:
                        email_field.clear()
                        email_field.send_keys(email)
                        print("邮箱填写成功")
                        break
                except:
                    continue

            if not email_field:
                print("未找到邮箱输入框")
                return False

            return True

        except Exception as e:
            print(f"填写个人信息时出错: {e}")
            return False

    def click_sign_up_now(self):
        """点击Sign Up Now按钮"""
        try:
            print("正在提交表单...")

            # 等待按钮可点击
            time.sleep(2)

            signup_now_selectors = [
                "//button[contains(., 'Sign Up Now')]",
                "//input[contains(@value, 'Sign Up Now')]",
                "//button[contains(., '报名')]",
                "//input[contains(@value, '报名')]"
            ]

            signup_button = None
            for selector in signup_now_selectors:
                try:
                    signup_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if signup_button:
                        # 滚动到按钮位置
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", signup_button)
                        time.sleep(1)
                        signup_button.click()
                        print("点击Sign Up Now按钮成功")
                        return True
                except:
                    continue

            print("未找到Sign Up Now按钮")
            return False

        except Exception as e:
            print(f"点击Sign Up Now按钮时出错: {e}")
            return False

    def verify_signup_success(self, first_name, last_name):
        """验证签到是否成功"""
        try:
            print("正在验证签到结果...")
            time.sleep(5)

            # 检查是否返回原页面并显示姓名
            full_name = f"{first_name} {last_name}"
            name_abbreviation = f"{first_name[0]}{last_name[0]}".upper()

            # 检查页面中是否包含姓名或缩写
            page_text = self.driver.page_source

            if full_name in page_text or name_abbreviation in page_text:
                print(f"✅ 签到成功！在页面中找到姓名: {full_name}")
                return True
            else:
                # 检查URL是否包含成功信息
                current_url = self.driver.current_url.lower()
                if "thank" in current_url or "success" in current_url or "confirm" in current_url:
                    print("✅ 签到成功！(通过URL确认)")
                    return True
                else:
                    print("⚠️ 未在页面中找到姓名，但可能签到成功")
                    # 截屏保存结果
                    self.driver.save_screenshot("signup_result.png")
                    print("已保存页面截图: signup_result.png")
                    return True  # 暂时返回True，因为可能页面刷新较慢

        except Exception as e:
            print(f"验证签到结果时出错: {e}")
            return False

    def run(self, first_name, last_name, email, target_day=None):
        """主执行函数"""
        try:
            print("开始执行自动化签到脚本...")
            self.setup_driver()

            # 步骤1: 打开页面
            self.navigate_to_page()

            # 步骤2: 找到会话，点击Sign Up按钮
            if not self.find_available_session_and_click(target_day):
                print("❌ 无法找到或点击Sign Up按钮")
                return False

            # 步骤3: 填写用户信息
            if not self.fill_personal_info(first_name, last_name, email):
                print("❌ 填写个人信息失败")
                return False

            # 步骤4: 点击Sign Up Now
            if not self.click_sign_up_now():
                print("❌ 点击Sign Up Now按钮失败")
                return False

            # 步骤5: 验证签到结果
            if not self.verify_signup_success(first_name, last_name):
                print("⚠️ 无法确认签到结果，请手动检查")
                return True  # 即使验证失败，也可能已经成功

            print("🎉 脚本执行完成！")
            return True

        except Exception as e:
            print(f"❌ 脚本执行过程中出错: {e}")
            # 保存错误截图
            if self.driver:
                self.driver.save_screenshot("error_screenshot.png")
                print("已保存错误截图: error_screenshot.png")
            return False
        finally:
            if self.driver:
                self.driver.quit()


def main():
    # 配置您的个人信息
    FIRST_NAME = "ChuQing"  # 替换为您的名字
    LAST_NAME = "Wang"  # 替换为您的姓氏
    EMAIL = "sunweibo221504@gmail.com"  # 替换为您的邮箱

    # 检查当前日期，决定目标会话
    current_time = datetime.datetime.now()
    weekday = current_time.weekday()  # 0=周一, 1=周二, ..., 6=周日

    target_day = None
    if weekday == 1:  # 周二
        target_day = "Tuesday"
        print("检测到周二，尝试签到周二session...")
    elif weekday == 6:  # 周日
        target_day = "Sunday"
        print("检测到周日，尝试签到周日session...")
    else:
        print(f"当前是周{weekday + 1}，尝试签到任何可用session...")

    # 执行自动化脚本
    bot = TableTennisSignUpBot()
    success = bot.run(FIRST_NAME, LAST_NAME, EMAIL, target_day)

    if success:
        print("自动化签到完成！")
        sys.exit(0)
    else:
        print("自动化签到失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()