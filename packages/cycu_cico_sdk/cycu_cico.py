import dataclasses
import datetime
import logging
import os
import re
import shutil
import stat
import urllib.parse
from typing import Any, Callable

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .constant import State, Url


@dataclasses.dataclass
class Status:
    date_time: datetime.datetime
    state: State


class SimpleCycuCico:
    def __init__(self, username: str, password: str):
        self.username: str = username
        self.password: str = password

        self.clean_up()
        edge_options: webdriver.EdgeOptions = webdriver.EdgeOptions()
        edge_options.add_argument(f"user-data-dir={os.getcwd()}")
        self.edge_driver: webdriver.Edge = webdriver.Edge(options=edge_options)
        self.login(username, password)

    @classmethod
    def clean_up(cls):
        def on_rm_error(func: Callable[[Any], None], path: str, exc_info: Any):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception as e:
                logging.exception(e)

        path: str
        for path in [
            'Ad Blocking',
            'BrowserMetrics',
            'CertificateRevocation',
            'Crashpad',
            'CrashpadMetrics-active.pma',
            'CrashpadMetrics.pma',
            'Default',
            'DevToolsActivePort',
            'Edge Shopping',
            'edge_shutdown_ms.txt',
            'First Run',
            'FirstLaunchAfterInstallation',
            'Functional Data',
            'Functional Data-wal',
            'Functional SAN Data',
            'Functional SAN Data-wal',
            'GrShaderCache',
            'Last Browser',
            'Last Version',
            'Local State',
            'OriginTrials',
            'RecoveryImproved',
            'Safe Browsing',
            'ShaderCache',
            'SmartScreen',
            'Speech Recognition',
            'Subresource Filter',
            'Trust Protection Lists',
            'Web Notifications Deny List',
            'WidevineCdm',
            'ZxcvbnData',
        ]:
            if not os.path.exists(path):
                continue

            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path, onerror=on_rm_error)
            else:
                try:
                    os.chmod(path, stat.S_IWRITE)
                    os.remove(path)
                except Exception as e:
                    logging.exception(e)

    def login(self, username: str, password: str):
        self.edge_driver.get(Url.BASE)

        d: webdriver.Edge
        WebDriverWait(self.edge_driver, 10).until(lambda d: d.find_element(By.NAME, 'UserNm'))
        self.edge_driver.find_element(By.NAME, 'UserNm').send_keys(username)
        self.edge_driver.find_element(By.NAME, 'UserPasswd').send_keys(password)
        self.edge_driver.find_element(By.NAME, 'UserPasswd').submit()

        WebDriverWait(self.edge_driver, 10).until(lambda d: d.find_element(By.ID, 'profile'))

    def get_status(self) -> Status:
        self.edge_driver.get(urllib.parse.urljoin(Url.BASE, Url.ATTENDANCE))

        d: webdriver.Edge
        WebDriverWait(self.edge_driver, 10).until(lambda d: d.find_element(By.ID, 'logTable'))

        log: str = self.edge_driver.find_element(By.ID, 'logTable').get_attribute('innerHTML')

        last_sign_date_time: str = re.search('[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}', log)[0]
        last_sign_state: str = re.search('無紙化平台簽.', log)[0]
        status: Status = Status(
            date_time=datetime.datetime.strptime(last_sign_date_time, '%Y-%m-%d %H:%M'),
            state=State.CLOCK_IN if '到' in last_sign_state else State.CLOCK_OUT)
        return status

    def clock(self, state: State):
        self.edge_driver.get(Url.BASE)

        d: webdriver.Edge
        WebDriverWait(self.edge_driver, 10).until(lambda d: d.find_element(By.CSS_SELECTOR, '.btn-primary'))

        if state == State.CLOCK_IN:
            self.edge_driver.find_element(By.CSS_SELECTOR, '.btn-primary').click()
        elif state == State.CLOCK_OUT:
            self.edge_driver.find_element(By.CSS_SELECTOR, '.btn-info').click()

        WebDriverWait(self.edge_driver, 10).until(
            lambda d: d.find_element(By.CSS_SELECTOR, '.swal2-styled.swal2-confirm'))

        self.edge_driver.find_element(By.CSS_SELECTOR, '.swal2-styled.swal2-confirm').click()