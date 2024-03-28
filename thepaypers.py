"""
Нагрузка плагина SPP

1/2 документ плагина
"""
import logging
import os
import time
from datetime import datetime
# import dateutil.parser
import dateparser
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.spp.types import SPP_document


class THEPAYPERS:
    """
    Класс парсера плагина SPP

    :warning Все необходимое для работы парсера должно находится внутри этого класса

    :_content_document: Это список объектов документа. При старте класса этот список должен обнулиться,
                        а затем по мере обработки источника - заполняться.


    """

    SOURCE_NAME = 'thepaypers'
    HOST = "https://thepaypers.com/news/all"
    _content_document: list[SPP_document]

    def __init__(self, webdriver: WebDriver, last_document: SPP_document = None, max_count_documents: int = 100, *args,
                 **kwargs):
        """
        Конструктор класса парсера

        По умолчанию внего ничего не передается, но если требуется (например: driver селениума), то нужно будет
        заполнить конфигурацию
        """
        # Обнуление списка
        self._content_document = []

        self.driver = webdriver
        self.max_count_documents = max_count_documents
        self.last_document = last_document
        self.wait = WebDriverWait(self.driver, timeout=20)

        # Логер должен подключаться так. Вся настройка лежит на платформе
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Parser class init completed")
        self.logger.info(f"Set source: {self.SOURCE_NAME}")
        ...

    def content(self) -> list[SPP_document]:
        """
        Главный метод парсера. Его будет вызывать платформа. Он вызывает метод _parse и возвращает список документов
        :return:
        :rtype:
        """
        self.logger.debug("Parse process start")
        try:
            self._parse()
        except Exception as e:
            self.logger.debug(f'Parsing stopped with error: {e}')
        else:
            self.logger.debug("Parse process finished")
        return self._content_document

    def _parse(self):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter to {self.HOST}")

        # ========================================
        # Тут должен находится блок кода, отвечающий за парсинг конкретного источника
        # -

        self.driver.get(url=self.HOST)
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.index_group')))

        while True:

            links = self.driver.find_elements(By.CLASS_NAME, 'details_rows')

            for link in links:

                web_link = link.find_element(By.TAG_NAME, 'h3').find_element(By.TAG_NAME, 'a').get_attribute('href')
                pub_date = dateparser.parse((link.find_element(By.CLASS_NAME, 'source').text.split(' | ')[1]))
                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[1])
                self.driver.get(web_link)
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.article')))
                self.logger.debug(f'Entered: {web_link}')

                title = self.driver.find_element(By.TAG_NAME, 'h1').text
                abstract = None
                text_content = self.driver.find_element(By.ID, 'pageContainer').text
                cat_list = self.driver.find_elements(By.XPATH,
                                                     '//table[contains(@class,\'category_table\')]//td[@class = \'source\']')
                for cat in cat_list:
                    # self.logger.debug(cat.text)
                    if cat.text == 'Keywords:':
                        try:
                            keywords = cat.find_element(By.XPATH, './following-sibling::td').text
                        except:
                            self.logger.exception('Keywords error')
                            keywords = ''
                    if cat.text == 'Categories:':
                        try:
                            categories = cat.find_element(By.XPATH, './following-sibling::td').text
                        except:
                            categories = ''
                    if cat.text == 'Companies:':
                        try:
                            companies = cat.find_element(By.XPATH, './following-sibling::td').text
                        except:
                            companies = ''
                    if cat.text == 'Countries:':
                        try:
                            countries = cat.find_element(By.XPATH, './following-sibling::td').text
                        except:
                            countries = ''

                other_data = {'keywords': keywords,
                              'categories': categories,
                              'companies': companies,
                              'countries': countries}

                doc = SPP_document(None,
                                   title,
                                   abstract,
                                   text_content,
                                   web_link,
                                   None,
                                   other_data,
                                   pub_date,
                                   datetime.now())

                self.find_document(doc)

                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

            try:
                next_pg_btn = self.driver.find_element(By.XPATH, '//a[@class = \'next\']')
                self.driver.execute_script('arguments[0].click()', next_pg_btn)
                time.sleep(3)
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.index_group')))
            except:
                self.logger.debug('No NEXT button')
                break
        # ---
        # ========================================
        ...

    def _encounter_pages(self) -> str:
        _base = self.URL
        _params = '&page='
        page = 0
        while True:
            url = _base + _params + str(page)
            page += 1
            yield url

    @staticmethod
    def _find_document_text_for_logger(self, doc: SPP_document):
        """
        Единый для всех парсеров метод, который подготовит на основе SPP_document строку для логера
        :param doc: Документ, полученный парсером во время своей работы
        :type doc:
        :return: Строка для логера на основе документа
        :rtype:
        """
        return f"Find document | name: {doc.title} | link to web: {doc.web_link} | publication date: {doc.pub_date}"

    def find_document(self, doc: SPP_document):
        """
        Метод для обработки найденного документа источника
        """
        if self.last_document and self.last_document.hash == _doc.hash:
            raise Exception(f"Find already existing document ({self.last_document})")

        self._content_document.append(doc)
        self.logger.info(self._find_document_text_for_logger(self,doc))

        if self.max_count_documents and len(self._content_document) >= self.max_count_documents:
            raise Exception(f"Max count articles reached ({self.max_count_documents})")
