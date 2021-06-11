# coding=utf-8
import os
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

HOSTS = {
    0: 'https://app.yinxiang.com',
    1: 'https://www.evernote.com',
    2: 'https://sandbox.yinxiang.com',
}


class TokenFetcher:
    def __init__(self, product_type, u, p):
        self.host = HOSTS[product_type]
        _option = webdriver.ChromeOptions()
        # _option.add_argument('--headless')
        _option.add_argument('--disable-gpu')
        # 本地web_driver
        # self.web_driver = webdriver.Chrome(chrome_options=_option)
        self.web_driver = webdriver.Remote(
            command_executor='http://127.0.0.1:4444/wd/hub',
            desired_capabilities=DesiredCapabilities().CHROME.copy())
        self.wait = WebDriverWait(self.web_driver, 5)
        self.u = u
        self.p = p.strip()

    def fetch_token(self):
        print('开始刷新开发者token...')
        self.web_driver.get(self.host + '/Login.action?targetUrl=%2Fapi%2FDeveloperToken.action')
        user_input = self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '#username')))
        user_input.send_keys(self.u)
        sleep(0.5)

        submit_button = self.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, '#loginButton')))
        submit_button.click()
        sleep(0.5)

        try:
            user_input = self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '#password')))
            user_input.send_keys(self.p)
            sleep(0.5)
            submit_button.click()
            sleep(1)

            remove_btn = self.web_driver.find_elements_by_name('remove')
            if remove_btn:
                remove_btn[0].click()
                sleep(0.5)

            self.web_driver.find_element_by_name('create').click()

            return self.web_driver.find_element_by_name('accessToken').get_attribute('value')
        finally:
            self.web_driver.quit()


if __name__ == '__main__':
    print(TokenFetcher(2, os.getenv("LEN_SB_EMAIL"), os.getenv("LEN_SB_PWD")).fetch_token())
