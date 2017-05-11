# just for testing xpath

import json
from scrapy.selector import Selector

with open('word_page.html', 'r+b') as f:
     bytes = f.read()
     text = bytes.decode('utf-8')
     text = Selector(text=text).xpath('//pre/text()').extract()[0]
     print(text)
     word_list = json.loads(text)
     print('total={}, page={}'.format(word_list['total'], word_list['page']))
     for dict_item in word_list['rows']:
          print(dict_item['id'])