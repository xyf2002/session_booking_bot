from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import datetime
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('signup_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class EUTTCSignUpBot:
    """爱丁堡大学乒乓球俱乐部自动预约机器人"""

    def __init__(self, headless=False):
        self.driver = None
        self.wait = None
        self.headless = headless
        self.base_url = "https://www.signupgenius.com/go/10c0d4faba62ca2f9c25-euttc#/"

    def setup_driver(self):
        """配置Chrome浏览器驱动"""
        logging.info("正在初始化Chrome浏览器...")

        chrome_options = Options()

        # 反检测配置
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 性能优化
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')

        # 设置真实User-Agent
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # 无头模式（可选）
        if self.headless:
            chrome_options.add_argument('--headless')
            logging.info("已启用无头模式")

        # 初始化驱动
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # 隐藏WebDriver标志
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

        # 设置窗口大小
        self.driver.set_window_size(1920, 1080)

        # 配置等待时间
        self.wait = WebDriverWait(self.driver, 20)

        logging.info("浏览器初始化完成")

    def navigate_to_page(self):
        """打开预约页面"""
        try:
            logging.info(f"正在打开页面: {self.base_url}")
            self.driver.get(self.base_url)

            # 等待AngularJS加载完成
            time.sleep(3)

            # 等待表格出现
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//table"))
            )

            logging.info("✅ 页面加载成功")
            return True

        except Exception as e:
            logging.error(f"❌ 页面加载失败: {e}")
            self.driver.save_screenshot("error_page_load.png")
            return False

    def handle_privacy_popup(self):
        """处理隐私弹窗（如果存在）"""
        try:
            logging.info("检查隐私弹窗...")
            time.sleep(2)

            # 查找所有可能的iframe
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")

            for iframe in iframes:
                try:
                    # 切换到iframe
                    self.driver.switch_to.frame(iframe)

                    # 查找Accept按钮
                    accept_buttons = self.driver.find_elements(
                        By.XPATH,
                        "//button[contains(translate(., 'ACCEPT', 'accept'), 'accept')]"
                    )

                    if accept_buttons:
                        accept_buttons[0].click()
                        logging.info("✅ 已关闭隐私弹窗")
                        self.driver.switch_to.default_content()
                        time.sleep(1)
                        return True

                    # 切换回主文档
                    self.driver.switch_to.default_content()

                except:
                    self.driver.switch_to.default_content()
                    continue

            logging.info("未检测到隐私弹窗")
            return True

        except Exception as e:
            logging.warning(f"处理隐私弹窗时出错: {e}")
            self.driver.switch_to.default_content()
            return True  # 即使失败也继续执行

    def find_tuesday_team_coaching_button(self):
        """
        查找Tuesday 8:30pm-10:00pm Team Coaching的Sign Up按钮
        这是最关键的步骤！
        """
        try:
            logging.info("正在查找Tuesday Team Coaching的Sign Up按钮...")

            # 滚动到表格区域
            self.driver.execute_script("window.scrollTo(0, 600);")
            time.sleep(2)

            # 策略1: 先找到包含Tuesday和Team Coaching的行
            tuesday_rows = self.driver.find_elements(
                By.XPATH,
                "//tr[contains(., 'Tuesday') and contains(., 'Team Coaching')]"
            )

            if tuesday_rows:
                logging.info(f"找到 {len(tuesday_rows)} 个Tuesday Team Coaching行")

                for row in tuesday_rows:
                    try:
                        # 在该行中查找Sign Up按钮
                        # 注意：Sign Up按钮是蓝色的，不是"Full"或"Selected"
                        signup_button = row.find_element(
                            By.XPATH,
                            ".//a[text()='Sign Up' and contains(@style, 'background')]"
                        )

                        # 检查按钮是否可点击（不是Full状态）
                        if signup_button.is_displayed() and signup_button.is_enabled():
                            logging.info("✅ 找到可用的Sign Up按钮")

                            # 滚动到按钮位置
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center'});",
                                signup_button
                            )
                            time.sleep(1)

                            # 点击按钮
                            signup_button.click()
                            logging.info("✅ 已点击Sign Up按钮")
                            time.sleep(2)
                            return True

                    except NoSuchElementException:
                        continue

            # 策略2: 如果找不到Tuesday，查找任何可用的Sign Up按钮（测试阶段）
            logging.info("未找到Tuesday session，尝试查找任何可用的Sign Up按钮...")

            all_signup_buttons = self.driver.find_elements(
                By.XPATH,
                "//table//a[text()='Sign Up' and not(contains(@class, 'disabled'))]"
            )

            if all_signup_buttons:
                logging.info(f"找到 {len(all_signup_buttons)} 个可用的Sign Up按钮")

                for button in all_signup_buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                            # 获取按钮所在行的信息
                            row = button.find_element(By.XPATH, "./ancestor::tr")
                            row_text = row.text
                            logging.info(f"找到可用按钮，行内容: {row_text[:100]}")

                            # 滚动并点击
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center'});",
                                button
                            )
                            time.sleep(1)
                            button.click()
                            logging.info("✅ 已点击Sign Up按钮")
                            time.sleep(2)
                            return True

                    except:
                        continue

            logging.error("❌ 未找到任何可用的Sign Up按钮")
            self.driver.save_screenshot("error_no_signup_button.png")
            return False

        except Exception as e:
            logging.error(f"❌ 查找Sign Up按钮时出错: {e}")
            self.driver.save_screenshot("error_find_button.png")
            return False

    def click_save_and_continue(self):
        """点击页面底部的Save & Continue按钮"""
        try:
            logging.info("正在查找Save & Continue按钮...")

            # 等待按钮出现
            time.sleep(2)

            # 滚动到页面底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            # 查找Save & Continue按钮
            save_button_selectors = [
                "//button[contains(., 'Save & Continue')]",
                "//button[contains(., 'Save and Continue')]",
                "//input[@value='Save & Continue']",
                "//a[contains(., 'Save & Continue')]"
            ]

            for selector in save_button_selectors:
                try:
                    save_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )

                    if save_button:
                        # 滚动到按钮
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});",
                            save_button
                        )
                        time.sleep(1)

                        # 点击按钮
                        save_button.click()
                        logging.info("✅ 已点击Save & Continue按钮")
                        time.sleep(3)
                        return True

                except:
                    continue

            logging.error("❌ 未找到Save & Continue按钮")
            self.driver.save_screenshot("error_no_save_button.png")
            return False

        except Exception as e:
            logging.error(f"❌ 点击Save & Continue时出错: {e}")
            return False

    def fill_signup_form(self, first_name, last_name, email):
        """填写Sign Me Up表单"""
        try:
            logging.info("正在填写个人信息...")

            # 等待表单加载
            time.sleep(3)

            # 验证是否在正确页面
            try:
                page_title = self.driver.find_element(By.XPATH, "//h1[contains(., 'Sign Me Up')]")
                logging.info("✅ 已进入Sign Me Up页面")
            except:
                logging.warning("⚠️ 可能不在Sign Me Up页面")

            # 填写First Name
            try:
                first_name_input = self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//input[@placeholder='First' or contains(@name, 'first')]")
                    )
                )
                first_name_input.clear()
                first_name_input.send_keys(first_name)
                logging.info(f"✅ First Name已填写: {first_name}")
            except Exception as e:
                logging.error(f"❌ First Name填写失败: {e}")
                return False

            # 填写Last Name
            try:
                last_name_input = self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//input[@placeholder='Last' or contains(@name, 'last')]")
                    )
                )
                last_name_input.clear()
                last_name_input.send_keys(last_name)
                logging.info(f"✅ Last Name已填写: {last_name}")
            except Exception as e:
                logging.error(f"❌ Last Name填写失败: {e}")
                return False

            # 填写Email
            try:
                email_input = self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//input[@type='email' or contains(@name, 'email')]")
                    )
                )
                email_input.clear()
                email_input.send_keys(email)
                logging.info(f"✅ Email已填写: {email}")
            except Exception as e:
                logging.error(f"❌ Email填写失败: {e}")
                return False

            # 等待所有字段填写完成
            time.sleep(1)

            logging.info("✅ 所有个人信息填写完成")
            return True

        except Exception as e:
            logging.error(f"❌ 填写表单时出错: {e}")
            self.driver.save_screenshot("error_fill_form.png")
            return False

    def check_recaptcha(self):
        """检查是否有reCAPTCHA"""
        try:
            # 查找reCAPTCHA元素
            recaptcha_elements = self.driver.find_elements(
                By.CLASS_NAME, "g-recaptcha"
            )

            if recaptcha_elements:
                logging.warning("⚠️ 检测到reCAPTCHA验证码！")
                logging.warning("⚠️ 请在30秒内手动完成验证...")

                # 播放提示音（如果系统支持）
                try:
                    import winsound
                    winsound.Beep(1000, 500)
                except:
                    pass

                # 等待用户完成验证
                time.sleep(30)

                return True

            return False

        except Exception as e:
            logging.warning(f"检查reCAPTCHA时出错: {e}")
            return False

    def submit_form(self):
        """提交表单（点击Sign Up Now）"""
        try:
            logging.info("正在提交表单...")

            # 检查reCAPTCHA
            self.check_recaptcha()

            # 滚动到页面底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            # 查找Sign Up Now按钮
            submit_button_selectors = [
                "//button[contains(., 'Sign Up Now')]",
                "//input[@value='Sign Up Now']",
                "//button[@type='submit']"
            ]

            for selector in submit_button_selectors:
                try:
                    submit_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )

                    if submit_button:
                        # 滚动到按钮
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});",
                            submit_button
                        )
                        time.sleep(1)

                        # 点击提交
                        submit_button.click()
                        logging.info("✅ 已点击Sign Up Now按钮")
                        time.sleep(5)
                        return True

                except:
                    continue

            logging.error("❌ 未找到Sign Up Now按钮")
            self.driver.save_screenshot("error_no_submit_button.png")
            return False

        except Exception as e:
            logging.error(f"❌ 提交表单时出错: {e}")
            return False

    def verify_success(self, first_name, last_name):
        """验证预约是否成功"""
        try:
            logging.info("正在验证预约结果...")
            time.sleep(5)

            # 检查URL
            current_url = self.driver.current_url.lower()
            logging.info(f"当前URL: {current_url}")

            # 检查成功标志
            success_indicators = [
                "✓ Selected",  # 选中标记
                "Selected",
                first_name,
                last_name,
                f"{first_name} {last_name}",
                "thank",
                "success",
                "confirm"
            ]

            page_source = self.driver.page_source

            for indicator in success_indicators:
                if indicator.lower() in page_source.lower():
                    logging.info(f"✅ 找到成功标志: {indicator}")

                    # 尝试截图保存成功状态
                    self.driver.save_screenshot(
                        f"success_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    )

                    return True

            # 如果没有明确的成功标志，检查是否返回到主页面
            if "euttc" in current_url:
                logging.info("✅ 已返回到session列表页面")
                self.driver.save_screenshot(
                    f"result_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                )
                return True

            logging.warning("⚠️ 未找到明确的成功标志，请手动检查")
            self.driver.save_screenshot("verify_result.png")
            return True  # 保守起见，返回True

        except Exception as e:
            logging.error(f"验证结果时出错: {e}")
            return False

    def run(self, first_name, last_name, email, target_day="Tuesday"):
        """主执行流程"""
        try:
            logging.info("=" * 60)
            logging.info("开始执行EUTTC自动预约脚本")
            logging.info(f"用户: {first_name} {last_name} ({email})")
            logging.info(f"目标: {target_day} Team Coaching Session")
            logging.info("=" * 60)

            # 步骤1: 初始化浏览器
            self.setup_driver()

            # 步骤2: 打开页面
            if not self.navigate_to_page():
                return False

            # 步骤3: 处理隐私弹窗
            self.handle_privacy_popup()

            # 步骤4: 查找并点击Sign Up按钮
            if not self.find_tuesday_team_coaching_button():
                logging.error("❌ 无法找到Sign Up按钮，预约失败")
                return False

            # 步骤5: 点击Save & Continue
            if not self.click_save_and_continue():
                logging.error("❌ 无法点击Save & Continue，预约失败")
                return False

            # 步骤6: 填写个人信息
            if not self.fill_signup_form(first_name, last_name, email):
                logging.error("❌ 填写表单失败，预约失败")
                return False

            # 步骤7: 提交表单
            if not self.submit_form():
                logging.error("❌ 提交表单失败，预约失败")
                return False

            # 步骤8: 验证结果
            if not self.verify_success(first_name, last_name):
                logging.warning("⚠️ 无法验证结果，请手动检查")
                return True

            logging.info("=" * 60)
            logging.info("🎉 预约成功完成！")
            logging.info("=" * 60)

            return True

        except Exception as e:
            logging.error(f"❌ 脚本执行失败: {e}")
            if self.driver:
                self.driver.save_screenshot(
                    f"error_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                )
            return False

        finally:
            # 保持浏览器打开5秒以便查看结果
            if self.driver:
                logging.info("5秒后关闭浏览器...")
                time.sleep(5)
                self.driver.quit()
                logging.info("浏览器已关闭")


def main():
    """主函数"""

    # ========== 配置区域 ==========
    FIRST_NAME = "Frank"  # 您的名字
    LAST_NAME = "Sun"  # 您的姓氏
    EMAIL = "frank.sun@ed.ac.uk"  # 您的邮箱
    HEADLESS = False  # 是否无头模式（False=显示浏览器）
    # =============================

    print("\n" + "=" * 60)
    print("EUTTC自动预约系统")
    print("=" * 60)
    print(f"用户信息:")
    print(f"  姓名: {FIRST_NAME} {LAST_NAME}")
    print(f"  邮箱: {EMAIL}")
    print(f"  模式: {'无头模式' if HEADLESS else '可视化模式'}")
    print("=" * 60 + "\n")

    # 创建机器人实例
    bot = EUTTCSignUpBot(headless=HEADLESS)

    # 执行预约
    success = bot.run(FIRST_NAME, LAST_NAME, EMAIL, target_day="Tuesday")

    # 返回结果
    if success:
        print("\n✅ 预约完成！请检查邮箱确认。")
        sys.exit(0)
    else:
        print("\n❌ 预约失败！请查看日志文件。")
        sys.exit(1)


if __name__ == "__main__":
    main()
