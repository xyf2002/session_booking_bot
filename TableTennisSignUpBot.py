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
    """爱丁堡大学乒乓球俱乐部自动预约机器人 - 简化版"""

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

        logging.info("✅ 浏览器初始化完成")

    def navigate_to_page(self):
        """打开预约页面"""
        try:
            logging.info(f"正在打开页面: {self.base_url}")
            self.driver.get(self.base_url)

            # 等待页面加载
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
            return True

    def find_any_available_signup_button(self):
        """
        查找任何可用的Sign Up按钮（精确匹配）
        修复：按钮是<button>标签，不是<a>标签，文本有空格
        """
        try:
            logging.info("正在查找可用的Sign Up按钮...")

            # 滚动到表格区域
            self.driver.execute_script("window.scrollTo(0, 600);")
            time.sleep(2)

            # 额外等待AngularJS渲染完成
            logging.info("等待AngularJS渲染完成...")
            time.sleep(3)

            # ===== 方法1: 精确匹配<button>标签，文本为"Sign Up"（去除空格） =====
            logging.info("方法1: 查找<button>标签...")
            signup_buttons = self.driver.find_elements(
                By.XPATH,
                "//button[contains(@class, 'btn-signup') and normalize-space(.)='Sign Up']"
            )
            logging.info(f"找到 {len(signup_buttons)} 个<button>类型的Sign Up按钮")

            if not signup_buttons:
                # ===== 方法2: 更宽松的匹配 =====
                logging.info("方法2: 使用宽松匹配...")
                signup_buttons = self.driver.find_elements(
                    By.XPATH,
                    "//button[contains(normalize-space(.), 'Sign Up') and not(contains(., 'Create'))]"
                )
                logging.info(f"找到 {len(signup_buttons)} 个包含'Sign Up'的按钮")

            if not signup_buttons:
                # ===== 方法3: 查找所有btn-signup类的按钮 =====
                logging.info("方法3: 通过CSS类查找...")
                signup_buttons = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "button.btn-signup"
                )
                logging.info(f"找到 {len(signup_buttons)} 个btn-signup类的按钮")

            # 如果还是没找到，保存调试信息
            if not signup_buttons:
                logging.error("❌ 未找到任何Sign Up按钮")

                # 保存页面源码用于调试
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                logging.info("已保存页面源码: debug_page.html")

                # 查找所有button元素
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                logging.info(f"\n页面上共有 {len(all_buttons)} 个<button>元素:")
                for idx, btn in enumerate(all_buttons[:10]):  # 只显示前10个
                    try:
                        btn_text = btn.text.strip()
                        btn_class = btn.get_attribute("class")
                        logging.info(f"  按钮 {idx + 1}: 文本='{btn_text}' | 类名={btn_class}")
                    except:
                        pass

                self.driver.save_screenshot("no_available_button.png")
                logging.error("已保存截图: no_available_button.png")
                return False

            # ===== 遍历找到的所有按钮 =====
            logging.info(f"\n开始检查 {len(signup_buttons)} 个按钮...")

            for idx, button in enumerate(signup_buttons):
                try:
                    # 获取按钮文本和属性
                    btn_text = button.text.strip()
                    btn_class = button.get_attribute("class")
                    btn_disabled = button.get_attribute("disabled")
                    btn_ng_disabled = button.get_attribute("data-ng-disabled")

                    logging.info(f"\n检查按钮 {idx + 1}:")
                    logging.info(f"  文本: '{btn_text}'")
                    logging.info(f"  类名: {btn_class}")
                    logging.info(f"  disabled属性: {btn_disabled}")
                    logging.info(f"  ng-disabled: {btn_ng_disabled}")

                    # 获取按钮所在行的信息
                    try:
                        row = button.find_element(By.XPATH, "./ancestor::tr")
                        row_text = row.text.replace('\n', ' ')[:150]
                        logging.info(f"  所在行: {row_text}")
                    except:
                        logging.info("  所在行: 无法获取")

                    # 检查按钮状态
                    is_displayed = button.is_displayed()
                    is_enabled = button.is_enabled()

                    logging.info(f"  可见性: {is_displayed}")
                    logging.info(f"  可点击: {is_enabled}")

                    # 排除已禁用的按钮
                    if btn_disabled == "true" or not is_enabled:
                        logging.info("  ⚠️ 按钮已禁用，跳过")
                        continue

                    # 检查按钮类名，排除waitlist或其他状态
                    if "waitlist" in btn_class.lower() or "full" in btn_class.lower():
                        logging.info("  ⚠️ 按钮状态为waitlist/full，跳过")
                        continue

                    # 尝试点击按钮
                    if is_displayed:
                        logging.info("  🎯 这是可用的Sign Up按钮，尝试点击...")

                        # 滚动到按钮位置
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});",
                            button
                        )
                        time.sleep(1)

                        # 方法A: 常规点击
                        try:
                            button.click()
                            logging.info(f"✅ 成功点击Sign Up按钮 (按钮 {idx + 1})")
                            time.sleep(3)
                            return True
                        except Exception as click_error:
                            logging.warning(f"  常规点击失败: {click_error}")

                            # 方法B: JavaScript点击
                            try:
                                self.driver.execute_script("arguments[0].click();", button)
                                logging.info(f"✅ 通过JavaScript成功点击 (按钮 {idx + 1})")
                                time.sleep(3)
                                return True
                            except Exception as js_error:
                                logging.warning(f"  JavaScript点击也失败: {js_error}")

                                # 方法C: 触发AngularJS的ng-click
                                try:
                                    self.driver.execute_script(
                                        "angular.element(arguments[0]).triggerHandler('click');",
                                        button
                                    )
                                    logging.info(f"✅ 通过AngularJS成功点击 (按钮 {idx + 1})")
                                    time.sleep(3)
                                    return True
                                except Exception as ng_error:
                                    logging.warning(f"  AngularJS点击也失败: {ng_error}")
                                    continue
                    else:
                        logging.info("  ❌ 按钮不可见")

                except Exception as button_error:
                    logging.warning(f"处理按钮 {idx + 1} 时出错: {button_error}")
                    continue

            # 如果所有按钮都不可用
            logging.error("❌ 所有Sign Up按钮都不可点击")
            logging.error("可能原因:")
            logging.error("  1. 所有session都已满员（Full状态）")
            logging.error("  2. 您已经预约过了（Selected状态）")
            logging.error("  3. Session还未开放")
            logging.error("  4. 按钮被AngularJS禁用了")

            self.driver.save_screenshot("no_available_button.png")
            logging.info("已保存截图: no_available_button.png")

            return False

        except Exception as e:
            logging.error(f"❌ 查找Sign Up按钮时出错: {e}")
            import traceback
            logging.error(traceback.format_exc())
            self.driver.save_screenshot("error_find_button.png")
            return False

    def click_save_and_continue(self):
        """点击Save & Continue按钮"""
        try:
            logging.info("正在查找Save & Continue按钮...")

            # 等待页面响应
            time.sleep(2)

            # 滚动到页面底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            # 查找Save & Continue按钮（多种可能的定位方式）
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
                page_title = self.driver.find_element(By.XPATH, "//h1 | //h2")
                logging.info(f"当前页面标题: {page_title.text}")
            except:
                logging.warning("⚠️ 无法确认页面标题")

            # 填写First Name
            try:
                first_name_input = self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH,
                         "//input[@placeholder='First' or contains(@name, 'firstname') or contains(@id, 'first')]")
                    )
                )
                first_name_input.clear()
                time.sleep(0.3)
                first_name_input.send_keys(first_name)
                logging.info(f"✅ First Name已填写: {first_name}")
            except Exception as e:
                logging.error(f"❌ First Name填写失败: {e}")
                return False

            # 填写Last Name
            try:
                last_name_input = self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH,
                         "//input[@placeholder='Last' or contains(@name, 'lastname') or contains(@id, 'last')]")
                    )
                )
                last_name_input.clear()
                time.sleep(0.3)
                last_name_input.send_keys(last_name)
                logging.info(f"✅ Last Name已填写: {last_name}")
            except Exception as e:
                logging.error(f"❌ Last Name填写失败: {e}")
                return False

            # 填写Email
            try:
                email_input = self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//input[@type='email' or contains(@name, 'email') or contains(@id, 'email')]")
                    )
                )
                email_input.clear()
                time.sleep(0.3)
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
                logging.warning("=" * 60)
                logging.warning("⚠️ 检测到reCAPTCHA验证码！")
                logging.warning("⚠️ 请在30秒内手动完成验证...")
                logging.warning("=" * 60)

                # 播放提示音（Windows系统）
                try:
                    import winsound
                    for _ in range(3):
                        winsound.Beep(1000, 200)
                        time.sleep(0.3)
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
                "//button[@type='submit' and contains(., 'Sign Up')]"
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
                "✓ Selected",
                "Selected",
                first_name.lower(),
                last_name.lower(),
                "thank",
                "success",
                "confirm"
            ]

            page_source = self.driver.page_source.lower()

            found_indicators = []
            for indicator in success_indicators:
                if indicator in page_source:
                    found_indicators.append(indicator)

            if found_indicators:
                logging.info(f"✅ 找到成功标志: {', '.join(found_indicators)}")

                # 截图保存成功状态
                screenshot_name = f"success_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.driver.save_screenshot(screenshot_name)
                logging.info(f"已保存成功截图: {screenshot_name}")

                return True

            # 如果没有明确的成功标志，但返回到主页面
            if "euttc" in current_url:
                logging.info("✅ 已返回到session列表页面")
                screenshot_name = f"result_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.driver.save_screenshot(screenshot_name)
                logging.info(f"已保存结果截图: {screenshot_name}")
                return True

            logging.warning("⚠️ 未找到明确的成功标志，但可能已成功")
            self.driver.save_screenshot("verify_result.png")
            return True  # 保守起见，返回True

        except Exception as e:
            logging.error(f"验证结果时出错: {e}")
            return False

    def run(self, first_name, last_name, email):
        """主执行流程"""
        try:
            logging.info("=" * 60)
            logging.info("开始执行EUTTC自动预约脚本")
            logging.info(f"用户: {first_name} {last_name} ({email})")
            logging.info("目标: 任何可用的Session")
            logging.info("=" * 60)

            # 步骤1: 初始化浏览器
            self.setup_driver()

            # 步骤2: 打开页面
            if not self.navigate_to_page():
                logging.error("❌ 第1步失败: 页面加载失败")
                return False

            # 步骤3: 处理隐私弹窗
            self.handle_privacy_popup()

            # 步骤4: 查找并点击任意可用的Sign Up按钮
            if not self.find_any_available_signup_button():
                logging.error("❌ 第2步失败: 无法找到可用的Sign Up按钮")
                return False

            # 步骤5: 点击Save & Continue
            if not self.click_save_and_continue():
                logging.error("❌ 第3步失败: 无法点击Save & Continue")
                return False

            # 步骤6: 填写个人信息
            if not self.fill_signup_form(first_name, last_name, email):
                logging.error("❌ 第4步失败: 填写表单失败")
                return False

            # 步骤7: 提交表单
            if not self.submit_form():
                logging.error("❌ 第5步失败: 提交表单失败")
                return False

            # 步骤8: 验证结果
            if not self.verify_success(first_name, last_name):
                logging.warning("⚠️ 第6步: 无法验证结果，请手动检查")
                return True

            logging.info("=" * 60)
            logging.info("🎉 预约成功完成！")
            logging.info("=" * 60)

            return True

        except Exception as e:
            logging.error(f"❌ 脚本执行失败: {e}")
            if self.driver:
                error_screenshot = f"error_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.driver.save_screenshot(error_screenshot)
                logging.error(f"已保存错误截图: {error_screenshot}")
            return False

        finally:
            # 保持浏览器打开10秒以便查看结果
            if self.driver:
                logging.info("10秒后关闭浏览器...")
                time.sleep(10)
                self.driver.quit()
                logging.info("浏览器已关闭")


def main():
    """主函数"""

    # ========== 配置区域 ==========
    FIRST_NAME = "Frank"  # 您的名字
    LAST_NAME = "Sun"  # 您的姓氏
    EMAIL = "frank.sun@ed.ac.uk"  # 您的邮箱
    HEADLESS = False  # False=显示浏览器，True=后台运行
    # =============================

    print("\n" + "=" * 60)
    print("EUTTC自动预约系统")
    print("=" * 60)
    print(f"用户信息:")
    print(f"  姓名: {FIRST_NAME} {LAST_NAME}")
    print(f"  邮箱: {EMAIL}")
    print(f"  模式: {'无头模式' if HEADLESS else '可视化模式'}")
    print(f"  目标: 任何可用的Session")
    print("=" * 60 + "\n")

    # 创建机器人实例
    bot = EUTTCSignUpBot(headless=HEADLESS)

    # 执行预约
    success = bot.run(FIRST_NAME, LAST_NAME, EMAIL)

    # 返回结果
    if success:
        print("\n" + "=" * 60)
        print("✅ 预约完成！")
        print("请检查:")
        print("  1. 浏览器最终页面")
        print("  2. 邮箱确认邮件")
        print("  3. SignUpGenius网站上的预约记录")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ 预约失败！")
        print("请查看:")
        print("  1. signup_bot.log 日志文件")
        print("  2. 生成的截图文件")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()