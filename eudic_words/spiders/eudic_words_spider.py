from urllib import parse

import scrapy
from eudic_words.items import EudicWordsItem
from urllib.parse import urlunparse
from scrapy.http.cookies import CookieJar
import scrapy_splash
import json
from getpass import getpass

script = """
function main(splash)
  splash:init_cookies(splash.args.cookies)
  assert(splash:go{
    splash.args.url,
    headers=splash.args.headers,
    http_method=splash.args.http_method,
    body=splash.args.body,
    })
  assert(splash:wait(0.5))

  local entries = splash:history()
  local last_response = entries[#entries].response
  return {
    url = splash:url(),
    headers = last_response.headers,
    http_status = last_response.status,
    cookies = splash:get_cookies(),
    html = splash:html(),
  }
end
"""


class EudicWordsSpider(scrapy.Spider):
    name = 'eudic_words_spider'
    allowed_domain = ['dict.eudic.net']
    start_urls = ['http://dict.eudic.net/account/login']
    cookie_jar = CookieJar()
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'dict.eudic.net',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Pragma': 'no-cache',
        'DNT': 1,
    }

    headers_word = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'DNT': 1,
        'Host': 'dict.eudic.net',
        'Pragma': 'no-cache',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

    form_data = {
        'UserName': '用户名',
        'Password': '密码',
        #CaptchaDeText: 09f95ce4ad2e4a25a35d3a6bfdc1925b
        #CaptchaInputText: sbqh
        'returnUrl': '/StudyList'
    }

    def start_requests(self):
        # input username and passwd
        self.form_data['UserName'] = input('Username: ')
        self.form_data['Password'] = getpass('Password: ')

        # start login
        return [scrapy.Request(url='http://dict.eudic.net/account/login',
                               headers=self.headers,
                               meta={
                                   'cookiejar': self.cookie_jar,
                               },
                               callback=self.parse_login)]

    def parse_login(self, response):

        # untested, cant make sure captcha image part work
        if b'CaptchaImage' in response.body:
            # deal with captcha
            print('copy the link:')
            link = response.xpath('//img[@class="CaptchaImage"]/@src').extract()[0]
            print(link)
            query = parse.urlparse(link).query
            captchaDeText = parse.parse_qs(query, True)['t']
            captchaInputText = input('CaptchaInputText: ')
            self.form_data['CaptchaInputText'] = captchaDeText
            self.form_data['CaptchaInputText'] = captchaInputText

        return scrapy_splash.SplashFormRequest.from_response(response,
                                                             callback=self.after_login,
                                                             formdata=self.form_data,
                                                             headers=self.headers,
                                                             endpoint='execute',
                                                             cache_args=['lua_source'],
                                                             args={
                                                               'lua_source': script
                                                             },
                                                             meta={
                                                                 'cookiejar': response.meta['cookiejar']
                                                             })



    def after_login(self, response):
        #with open('login_page.html', 'w+b') as f:
        #    f.write(response.body)

        # http://dict.eudic.net/StudyList/GridData?catid=&_search=false&rows=5&page=1&sidx=&sord=asc
        url = urlunparse(('http', 'dict.eudic.net', '/StudyList/GridData', '',
                    'catid=&_search=false&rows=50&page=1&sidx=&sord=asc', ''))

        return scrapy_splash.SplashRequest(url=url,
                                           callback=self.parse_word,
                                           headers=self.headers_word,
                                           endpoint='execute',
                                           cache_args=['lua_source'],
                                           args={
                                               'lua_source': script
                                           },
                                           meta={
                                               'cookiejar': response.meta['cookiejar']
                                           })

    def parse_word(self, response):
        #with open('word_page.html', 'w+b') as f:
        #   f.write(response.body)

        # get json from html
        json_text = response.xpath('//pre/text()').extract()[0]

        # get words
        data_dict = json.loads(json_text)
        total = data_dict['total']
        page = data_dict['page']

        # check if next page exist
        if page < total:
            url = urlunparse(('http', 'dict.eudic.net', '/StudyList/GridData', '',
                              'catid=&_search=false&rows=50&page={}&sidx=&sord=asc'.format(page+1), ''))
            yield scrapy_splash.SplashRequest(url=url,
                                               callback=self.parse_word,
                                               headers=self.headers_word,
                                               endpoint='execute',
                                               cache_args=['lua_source'],
                                               args={
                                                   'lua_source': script
                                               },
                                               meta={
                                                   'cookiejar': response.meta['cookiejar']
                                               })

        # save word
        for word_dict in data_dict['rows']:
            word = EudicWordsItem()
            word['word'] = word_dict['id']
            yield word


