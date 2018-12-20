import os

import pymongo
import time
import logging

from pymongo.errors import DuplicateKeyError
from selenium import webdriver

import sys
sys.path.append('/root/WeiboSpider-master/sina')
from settings import LOCAL_MONGO_HOST, LOCAL_MONGO_PORT, DB_NAME
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from pyvirtualdisplay import Display


class LikesSpider:

    def __init__(self, collection_param, table_param):
        self.page_nums = 1
        self.tweets = None
        self.page = 1
        self.node = None
        self.count = 1
        self.collection = collection_param
        self.table = table_param

        # os.system('pkill -f phantom')
        # log_file = open('/root/firefox.log', 'w')
        # binary = FirefoxBinary('/usr/local/firefox/firefox', log_file = log_file)
        # capabilities_argument = DesiredCapabilities().FIREFOX
        # capabilities_argument["marionette"] = True
        # self.browser = webdriver.Firefox(firefox_binary=binary)
        # self.browser.set_window_size(1050, 840)
        os.system('pkill -f phantom')
        self.browser = webdriver.PhantomJS()
        self.browser.set_window_size(1050, 840)

    def page_nums_spider(self, uid):
        url = 'https://weibo.com/{}/like?page=1#feedtop'.format(uid)
        self.browser.get(url)
        self.browser.implicitly_wait(10)
        time.sleep(0.5)

        while True:
            #  两次下拉，获取全部信息
            try:
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(0.5)
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(0.5)
                break
            except Exception as e:
                logging.warning(e)

        #  获取节点id，获取不到则没有点赞微博
        try:
            self.browser.find_element_by_xpath('//*[@id="plc_main"]/div[2]/div[6]/div')
            self.node = self.browser.find_element_by_xpath('//*[@id="plc_main"]/div[2]/div[6]').get_attribute('id')
        except Exception as e:
            logging.warning(e)
            print("没有点赞的微博")
            self.node = None
            self.page_nums = None

        if self.node is not None:
            while True:
                #  获取点赞微博的总页数
                try:
                    page_nums = self.browser.find_element_by_xpath('//*[@id="{}"]/div[2]/div[3]/div[last()]/div/span/a'.format(self.node)).get_attribute('action-data').split('=')[2]
                    self.page_nums = int(page_nums)
                    self.page = 1
                    self.page_spider(uid)
                    break
                #  点赞微博只有一页，则没有总页数。且最后一条微博没有被删除
                except Exception as e:
                    if self.browser.find_element_by_xpath('//*[@id="{}"]/div[2]/div[3]/div[last()]'.format(self.node)).get_attribute('action-type') == "feed_list_item" \
                            or self.browser.find_element_by_xpath('//*[@id="{}"]/div[2]/div[3]/div[last()]/div[1]'.format(self.node)).get_attribute('action-type') == "feed_list_item":
                        self.page_spider(uid)
                        break
                    else:
                        if self.count < 5:
                            logging.warning(e)
                            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                            self.count = self.count + 1
                            time.sleep(1)
                        else:
                            print("加载失败!")
                            self.page_spider(uid)
                            break

        else:
            self.page_spider(uid)

    def page_spider(self, uid):
        while True:
            if self.page_nums is not None:
                print(self.page_nums)
                print('page=' + str(self.page))
                url = 'https://weibo.com/{}/like?page={}#feedtop'.format(uid, self.page)
                self.browser.implicitly_wait(10)
                self.browser.get(url)
                time.sleep(0.5)

                #  两次下拉，获取全部信息
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(0.5)
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(0.5)

                #  获取当前页的所有微博节点
                while True:
                    try:
                        self.tweets = self.browser.find_elements_by_xpath(
                            '//*[@id="{}"]/div[2]/div[3]/div'.format(self.node))
                        break
                    except Exception as e:
                        logging.warning(e)
                        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(1)

                #  获取每一条微博的信息
                if self.tweets is not None:
                    for tweet in self.tweets:
                        try:
                            if tweet.get_attribute('tbinfo'):
                                text = tweet.text.split('\n')
                                _id = uid + '-' + tweet.get_attribute('mid')
                                user_id = uid  # 点赞用户的id
                                like_id = tweet.get_attribute('tbinfo')[5:15]  # 点赞对象用户的id
                                like_nick_name = text[2]  # 点赞对象用户的昵称
                                content = ''.join([''.join(s.split()) for s in text[3:-5]])  # 点赞微博的内容
                                create_time = ''.join(text[-5].split(' ')[0:2])  # 点赞微博发表时间
                                if len(text[-3].split(' ')) > 1:
                                    repost_num = text[-3].split(' ')[1]  # 点赞微博的转发数
                                else:
                                    repost_num = '0'
                                if len(text[-2].split(' ')) > 1:
                                    comment_num = text[-2].split(' ')[1]  # 点赞微博的评论数
                                else:
                                    comment_num = '0'
                                like_num = text[-1]  # 点赞微博的点赞数
                                crawl_time = int(time.time())  # 抓取时间戳
                                try:
                                    self.collection.save(
                                        {"_id": _id, "user_id": user_id, "like_id": like_id, "like_nick_name": like_nick_name,
                                         "content": content, "create_time": create_time, "repost_num": repost_num,
                                         "comment_num": comment_num, "like_num": like_num, "crawl_time": crawl_time})
                                    print(_id)
                                except DuplicateKeyError as e:
                                    logging.warning(e)
                                    pass
                        except Exception as e:
                            logging.warning(e)
                            self.page = self.page - 1

                self.page = self.page + 1
                if self.page > self.page_nums:
                    break
            else:
                break

        self.count = 1
        try:
            self.table.update_one({'_id': uid}, {'$set': {'like_flag': 'true'}})
        except Exception as e:
            print(e)


if __name__ == "__main__":
    display = Display(visible=0, size=(800,600))
    display.start()
    mongo_client = pymongo.MongoClient(LOCAL_MONGO_HOST, LOCAL_MONGO_PORT)
    collection = mongo_client[DB_NAME]["Likes"]
    table = mongo_client[DB_NAME]["FollowedIDs"]

    # 查找一个已经爬取完微博信息的id
    while True:
        user = table.find_one({'tweet_flag': 'true', 'like_flag': 'false'})
        if user is not None:
            uid = user['_id']
            print('uid:' + uid)
            LikesSpider(collection, table).page_nums_spider(uid)
        else:
            print("暂时没有可爬取的id")
            time.sleep(10)
