from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import time
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
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        if self.headless:
            chrome_options.add_argument('--headless')
            logging.info("已启用无头模式")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })

        self.driver.set_window_size(800, 1200)
        self.wait = WebDriverWait(self.driver, 20)
        logging.info("✅ 浏览器初始化完成")

    def navigate_to_page(self):
        """打开预约页面"""
        try:
            logging.info(f"正在打开页面: {self.base_url}")
            self.driver.get(self.base_url)
            time.sleep(3)
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//table")))
            logging.info("✅ 页面加载成功")
            return True
        except Exception as e:
            logging.error(f"❌ 页面加载失败: {e}")
            self.driver.save_screenshot("error_page_load.png")
            return False

    def handle_privacy_popup(self):
        """处理隐私弹窗"""
        try:
            logging.info("检查隐私弹窗...")
            time.sleep(2)
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")

            for iframe in iframes:
                try:
                    self.driver.switch_to.frame(iframe)
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

    def find_tuesday_team_coaching_button(self):
        """查找Tuesday Team Coaching的Sign Up按钮（选择最后一个）"""
        try:
            logging.info("正在查找Tuesday Team Coaching的Sign Up按钮...")
            self.driver.execute_script("window.scrollTo(0, 600);")
            time.sleep(2)
            logging.info("等待AngularJS渲染完成...")
            time.sleep(3)

            # 策略1: 通过行内容精确定位
            logging.info("\n策略1: 通过表格行内容查找Tuesday + Team Coaching...")
            try:
                tuesday_rows = self.driver.find_elements(
                    By.XPATH,
                    "//tr[contains(., 'Tuesday') and contains(., 'Team Coaching')]"
                )
                logging.info(f"找到 {len(tuesday_rows)} 个Tuesday Team Coaching行")

                if len(tuesday_rows) == 0:
                    logging.warning("未找到任何Tuesday Team Coaching行")
                else:
                    # 打印所有找到的行
                    logging.info(f"⚠️ 发现{len(tuesday_rows)}个Tuesday Team Coaching行")
                    logging.info("将选择最后一个（最远的未来session）")

                    for idx, row in enumerate(tuesday_rows):
                        try:
                            row_text = row.text.replace('\n', ' ')[:200]
                            logging.info(f"  行 {idx + 1}: {row_text}")
                        except:
                            pass

                    # 始终选择最后一个
                    target_row = tuesday_rows[-1]  # -1 表示最后一个元素
                    logging.info(f"\n✅ 选择最后一个Tuesday Team Coaching行（第{len(tuesday_rows)}个）")

                    if self._try_click_row_button(target_row, f"策略1-最后一行(第{len(tuesday_rows)}个)"):
                        return True

            except Exception as e:
                logging.warning(f"策略1失败: {e}")

            # 策略2: 按钮索引
            logging.info("\n策略2: 尝试通过按钮索引定位...")
            try:
                all_signup_buttons = self.driver.find_elements(
                    By.XPATH,
                    "//button[contains(@class, 'btn-signup') and normalize-space(.)='Sign Up']"
                )
                logging.info(f"找到总共 {len(all_signup_buttons)} 个Sign Up按钮")

                for button_index in [8, 9, 10]:
                    if len(all_signup_buttons) > button_index:
                        target_button = all_signup_buttons[button_index]
                        try:
                            row = target_button.find_element(By.XPATH, "./ancestor::tr")
                            row_text = row.text.replace('\n', ' ')[:150]
                            logging.info(f"\n检查第{button_index + 1}个按钮: {row_text}")

                            if "tuesday" in row_text.lower() and "team coaching" in row_text.lower():
                                logging.info(f"✅ 第{button_index + 1}个按钮是Tuesday Team Coaching")
                                if self._try_click_button(target_button, f"策略2-第{button_index + 1}个"):
                                    return True
                        except:
                            pass
            except Exception as e:
                logging.warning(f"策略2失败: {e}")

            logging.error("❌ 所有策略都未能找到可用的Tuesday Team Coaching按钮")
            self.driver.save_screenshot("tuesday_not_found.png")
            return False

        except Exception as e:
            logging.error(f"❌ 查找Tuesday按钮时出错: {e}")
            return False

    def find_any_available_signup_button(self):
        """查找任何可用的Sign Up按钮"""
        try:
            logging.info("正在查找任意可用的Sign Up按钮...")
            self.driver.execute_script("window.scrollTo(0, 600);")
            time.sleep(2)
            time.sleep(3)

            signup_buttons = self.driver.find_elements(
                By.XPATH,
                "//button[contains(@class, 'btn-signup') and normalize-space(.)='Sign Up']"
            )
            logging.info(f"找到 {len(signup_buttons)} 个Sign Up按钮")

            for idx, button in enumerate(signup_buttons):
                try:
                    row = button.find_element(By.XPATH, "./ancestor::tr")
                    row_text = row.text.replace('\n', ' ')[:100]
                    logging.info(f"\n检查按钮 {idx + 1}: {row_text}")

                    if button.is_displayed() and button.is_enabled():
                        btn_disabled = button.get_attribute("disabled")
                        if btn_disabled != "true":
                            logging.info("  状态: 可点击 ✅")
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center'});", button
                            )
                            time.sleep(1)
                            if self._try_click_button(button, f"任意按钮-{idx + 1}"):
                                return True
                except:
                    continue

            logging.error("❌ 没有找到可用的Sign Up按钮")
            self.driver.save_screenshot("no_available_button.png")
            return False

        except Exception as e:
            logging.error(f"❌ 查找按钮时出错: {e}")
            return False

    def _try_click_row_button(self, row, strategy_name):
        """尝试点击指定行中的Sign Up按钮"""
        try:
            row_text = row.text.replace('\n', ' ')[:150]
            logging.info(f"\n尝试点击行的按钮 ({strategy_name}): {row_text}")

            signup_button = row.find_element(
                By.XPATH,
                ".//button[contains(@class, 'btn-signup') and normalize-space(.)='Sign Up']"
            )

            if not signup_button.is_displayed():
                logging.warning("  ⚠️ 按钮不可见")
                return False

            if not signup_button.is_enabled() or signup_button.get_attribute("disabled") == "true":
                logging.warning("  ⚠️ 按钮已禁用")
                return False

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", signup_button
            )
            time.sleep(1)
            return self._try_click_button(signup_button, strategy_name)

        except NoSuchElementException:
            logging.warning(f"  ⚠️ 该行中没有Sign Up按钮")
            return False
        except Exception as e:
            logging.warning(f"  处理行按钮时出错: {e}")
            return False

    def _try_click_button(self, button, strategy_name):
        """尝试多种方式点击按钮"""
        try:
            try:
                button.click()
                logging.info(f"✅ 成功点击按钮 ({strategy_name} - 常规点击)")
                time.sleep(3)
                return True
            except:
                try:
                    self.driver.execute_script("arguments[0].click();", button)
                    logging.info(f"✅ 成功点击按钮 ({strategy_name} - JS点击)")
                    time.sleep(3)
                    return True
                except:
                    try:
                        self.driver.execute_script(
                            "angular.element(arguments[0]).triggerHandler('click');", button
                        )
                        logging.info(f"✅ 成功点击按钮 ({strategy_name} - NG点击)")
                        time.sleep(3)
                        return True
                    except:
                        logging.warning(f"所有点击方法都失败")
                        return False
        except Exception as e:
            logging.error(f"点击按钮时出错: {e}")
            return False

    def click_save_and_continue(self):
        """点击Save & Continue按钮"""
        try:
            logging.info("正在查找Save & Continue按钮...")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            for selector in [
                "//button[contains(., 'Save & Continue')]",
                "//button[contains(., 'Save and Continue')]",
                "//input[@value='Save & Continue']"
            ]:
                try:
                    save_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    if save_button:
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", save_button
                        )
                        time.sleep(1)
                        save_button.click()
                        logging.info("✅ 已点击Save & Continue按钮")
                        time.sleep(3)
                        return True
                except:
                    continue

            logging.error("❌ 未找到Save & Continue按钮")
            return False
        except Exception as e:
            logging.error(f"❌ 点击Save & Continue时出错: {e}")
            return False

    def fill_signup_form(self, first_name, last_name, email):
        """填写表单"""
        try:
            logging.info("正在填写个人信息...")
            time.sleep(3)

            first_name_input = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@placeholder='First' or contains(@name, 'firstname')]")
                )
            )
            first_name_input.clear()
            time.sleep(0.3)
            first_name_input.send_keys(first_name)
            logging.info(f"✅ First Name已填写: {first_name}")

            last_name_input = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@placeholder='Last' or contains(@name, 'lastname')]")
                )
            )
            last_name_input.clear()
            time.sleep(0.3)
            last_name_input.send_keys(last_name)
            logging.info(f"✅ Last Name已填写: {last_name}")

            email_input = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@type='email' or contains(@name, 'email')]")
                )
            )
            email_input.clear()
            time.sleep(0.3)
            email_input.send_keys(email)
            logging.info(f"✅ Email已填写: {email}")

            time.sleep(1)
            logging.info("✅ 所有个人信息填写完成")
            return True

        except Exception as e:
            logging.error(f"❌ 填写表单时出错: {e}")
            self.driver.save_screenshot("error_fill_form.png")
            return False

    def submit_form(self):
        """提交表单"""
        try:
            logging.info("正在提交表单...")

            # 检查reCAPTCHA
            recaptcha_elements = self.driver.find_elements(By.CLASS_NAME, "g-recaptcha")
            if recaptcha_elements:
                logging.warning("⚠️ 检测到reCAPTCHA验证码！请在30秒内手动完成...")
                time.sleep(30)

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            for selector in [
                "//button[contains(., 'Sign Up Now')]",
                "//input[@value='Sign Up Now']",
                "//button[@type='submit' and contains(., 'Sign Up')]"
            ]:
                try:
                    submit_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    if submit_button:
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", submit_button
                        )
                        time.sleep(1)
                        submit_button.click()
                        logging.info("✅ 已点击Sign Up Now按钮")
                        time.sleep(5)
                        return True
                except:
                    continue

            logging.error("❌ 未找到Sign Up Now按钮")
            return False
        except Exception as e:
            logging.error(f"❌ 提交表单时出错: {e}")
            return False

    def verify_success(self, first_name, last_name):
        """验证预约是否成功"""
        try:
            logging.info("正在验证预约结果...")
            time.sleep(5)

            current_url = self.driver.current_url.lower()
            logging.info(f"当前URL: {current_url}")

            success_indicators = [
                "✓ selected", "selected", first_name.lower(),
                last_name.lower(), "thank", "success", "confirm"
            ]

            page_source = self.driver.page_source.lower()
            found_indicators = [ind for ind in success_indicators if ind in page_source]

            if found_indicators or "euttc" in current_url:
                logging.info(f"✅ 找到成功标志: {', '.join(found_indicators) if found_indicators else 'URL确认'}")
                screenshot_name = f"success_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.driver.save_screenshot(screenshot_name)
                logging.info(f"已保存成功截图: {screenshot_name}")
                return True

            logging.warning("⚠️ 未找到明确的成功标志")
            self.driver.save_screenshot("verify_result.png")
            return True

        except Exception as e:
            logging.error(f"验证结果时出错: {e}")
            return False

    def run(self, first_name, last_name, email, prefer_tuesday=True):
        """主执行流程"""
        try:
            logging.info("=" * 60)
            logging.info("开始执行EUTTC自动预约脚本")
            logging.info(f"用户: {first_name} {last_name} ({email})")
            logging.info(f"目标: {'Tuesday Team Coaching' if prefer_tuesday else '任意Session'}")
            logging.info("=" * 60)

            self.setup_driver()

            if not self.navigate_to_page():
                return False

            self.handle_privacy_popup()

            if prefer_tuesday:
                if not self.find_tuesday_team_coaching_button():
                    logging.warning("⚠️ 未找到Tuesday，尝试任意按钮...")
                    if not self.find_any_available_signup_button():
                        return False
            else:
                if not self.find_any_available_signup_button():
                    return False

            if not self.click_save_and_continue():
                return False

            if not self.fill_signup_form(first_name, last_name, email):
                return False

            if not self.submit_form():
                return False

            if not self.verify_success(first_name, last_name):
                logging.warning("⚠️ 无法验证结果")
                return True

            logging.info("=" * 60)
            logging.info("🎉 预约成功完成！")
            logging.info("=" * 60)
            return True

        except Exception as e:
            logging.error(f"❌ 脚本执行失败: {e}")
            if self.driver:
                self.driver.save_screenshot(f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            return False
        finally:
            if self.driver:
                logging.info("10秒后关闭浏览器...")
                time.sleep(10)
                self.driver.quit()


def main():
    # ========== 配置区域 ==========
    FIRST_NAME = "kratik"
    LAST_NAME = "virmani"
    EMAIL = "sunweibo221504@gmail.com"
    HEADLESS = False
    PREFER_TUESDAY = True  # True=优先Tuesday，False=任意session
    # =============================

    print("\n" + "=" * 60)
    print("EUTTC自动预约系统")
    print("=" * 60)
    print(f"姓名: {FIRST_NAME} {LAST_NAME}")
    print(f"邮箱: {EMAIL}")
    print(f"模式: {'无头' if HEADLESS else '可视化'}")
    print(f"目标: {'Tuesday Team Coaching' if PREFER_TUESDAY else '任意Session'}")
    print("=" * 60 + "\n")

    bot = EUTTCSignUpBot(headless=HEADLESS)
    success = bot.run(FIRST_NAME, LAST_NAME, EMAIL, prefer_tuesday=PREFER_TUESDAY)

    if success:
        print("\n✅ 预约完成！请检查邮箱确认。")
        sys.exit(0)
    else:
        print("\n❌ 预约失败！请查看日志文件。")
        sys.exit(1)


if __name__ == "__main__":
    main()