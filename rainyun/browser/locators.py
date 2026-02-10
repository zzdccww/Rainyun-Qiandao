"""页面定位符。"""

from selenium.webdriver.common.by import By

# 定位符常量化 (让维护更简单)
XPATH_CONFIG = {
    "LOGIN_BTN": "//button[@type='submit' and contains(., '登') and contains(., '录')]",
    # “每日签到”卡片根节点（便于读取卡片级文案，降低对局部结构的依赖）
    "SIGN_IN_CARD": "//div[contains(@class, 'card') and .//div[contains(@class, 'card-header') and .//span[contains(normalize-space(.), '每日签到')]]]",
    # “每日签到”卡片头部（不依赖按钮存在，用于读取当前状态文案）
    "SIGN_IN_HEADER": "//div[contains(@class, 'card-header') and .//span[contains(normalize-space(.), '每日签到')]]",
    # “每日签到”按钮：兼容 a/button 标签与常见文案变体
    "SIGN_IN_BTN": "//div[contains(@class, 'card-header') and .//span[contains(normalize-space(.), '每日签到')]]//*[self::a or self::button][contains(normalize-space(.), '领取奖励') or contains(normalize-space(.), '去完成') or contains(normalize-space(.), '去签到')]",
    # 验证码相关定位符统一为 (By, selector) 结构，避免 ID/XPath 混用
    "CAPTCHA_SUBMIT": (By.XPATH, "//div[@id='tcStatus']/div[2]/div[2]/div/div"),
    "CAPTCHA_RELOAD": (By.ID, "reload"),
    "CAPTCHA_BG": (By.ID, "slideBg"),
    "CAPTCHA_OP": (By.ID, "tcOperation"),
    "CAPTCHA_IMG_INSTRUCTION": (By.XPATH, "//div[@id='instruction']//img"),
}
