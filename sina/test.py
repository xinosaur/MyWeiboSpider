import time

import pymongo
import pandas as pd

# client = pymongo.MongoClient('localhost', 27017)
# db = client['Sina_test2']
# table = db['FollowedIDs']
# # table = db['UsedIds']
#
# data = table.find_one({'tweet_flag': 'true', 'like_flag': 'false'})
# print(data)
# table.update_one({'_id': data['_id']}, {'$set': {'flag': 'true'}})

# uid = table.find_one({'flag': 'false'})['_id']
# print(uid)

# table.insert_one({'_id', 'data_id'})

# used_ids = ['5499106103', '2005901751', '1844283341', '1197755162', '2833139360']
# table.insert_one({'_id': '5499106103'})
# table.save({'_id': '2005901751'})
# table.insert_one({'_id': '2005901751'})
# table.insert_one({'_id': '1844283341'})


# if table.find_one({'_id': '5499106103'}) is None:
#     print(table.find_one({'_id': '5499106103'}))

# used_ids = ['5499106103']
# for used_id in used_ids:
#     data = pd.DataFrame(list(table.find({'fan_id': used_id})))['followed_id']

# unused_ids = list(set(data).difference(set(used_ids)))
# print(unused_ids)

from selenium import webdriver

url = 'https://weibo.com/{}/like?page=1#feedtop'.format('2154491277')
browser = webdriver.PhantomJS(executable_path=r'C:\phantomjs-2.1.1-windows\bin\phantomjs.exe')
browser.set_window_size(1050, 840)
# browser.implicitly_wait(10)
browser.get(url)
time.sleep(2)

browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
time.sleep(1)
browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
time.sleep(1)

try:
    browser.find_element_by_xpath('//*[@id="plc_main"]/div[2]/div[6]/div')
    node = browser.find_element_by_xpath('//*[@id="plc_main"]/div[2]/div[6]').get_attribute('id')
    print(node)
except Exception as e:
    print(e)
    print("空")


# print('//*[@id="{}"]/div[2]/div[3]/div[46]/div/span/a'.format(node))
# page = browser.find_element_by_xpath('//*[@id="Pl_Core_LikesFeedV6__68"]/div[2]/div[3]/div[46]/div/span/a').get_attribute('action-data').split('=')[2]
# print(page)

while True:
    try:
        page_nums = browser.find_element_by_xpath('//*[@id="{}"]/div[2]/div[3]/div[last()]/div/span/a'.format(node)).get_attribute('action-data').split('=')[2]
        print(page_nums)
        break
    except Exception as e:
        print(e)
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
