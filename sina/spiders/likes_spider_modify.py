import os

import pymongo
import time
import logging

from pymongo.errors import DuplicateKeyError
from selenium import webdriver

from sina.settings import LOCAL_MONGO_HOST, LOCAL_MONGO_PORT, DB_NAME


class LikesSpider:

    def __init__(self, collection_param, table_param):
        self.page_nums = 1  # 用户微博总页数
        self.page = 1  # 当前爬取的微博页号
        self.node = None
        self.count = 1
        self.collection = collection_param  # Likes Document
        self.table = table_param  # FollowedIDs Document

        os.system('pkill -f phantom')
        self.browser = webdriver.PhantomJS(
            executable_path=r'C:\phantomjs-2.1.1-windows\bin\phantomjs.exe')
        self.browser.set_window_size(1050, 840)

        # self.url = 'https://weibo.com/{}/like?page=1#feedtop'.format(uid)
        # self.browser.get(self.url)
        # time.sleep(2)
        #
        # while True:
        #     #  两次下拉，获取全部信息
        #     try:
        #         self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        #         time.sleep(1)
        #         self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        #         time.sleep(1)
        #         break
        #     except Exception as e:
        #         print(e)
        #
        # #  获取节点id
        # try:
        #     self.browser.find_element_by_xpath('//*[@id="plc_main"]/div[2]/div[6]/div')
        #     self.node = self.browser.find_element_by_xpath('//*[@id="plc_main"]/div[2]/div[6]').get_attribute('id')
        # except Exception as e:
        #     print(e)
        #     print("没有点赞的微博")
        #     self.node = None
        #     self.page_spider(uid)
        #
        # #  获取点赞微博的总页数
        # if self.node is not None:
        #     while True:
        #         try:
        #             page_nums = self.browser.find_element_by_xpath('//*[@id="{}"]/div[2]/div[3]/div[last()]/div/span/a'.format(self.node)).get_attribute('action-data').split('=')[2]
        #             self.page_nums = int(page_nums)
        #             self.page_spider(uid)
        #             break
        #         except Exception as e:
        #             if self.browser.find_element_by_xpath('//*[@id="{}"]/div[2]/div[3]/div[last()]'.format(self.node)).get_attribute('action-type') == "feed_list_item":
        #                 self.page_nums = 1
        #                 self.page_spider(uid)
        #             else:
        #                 logging.warning(e)
        #                 # self.browser.get(self.url)
        #                 # self.browser.implicitly_wait(10)
        #                 # self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        #                 # time.sleep(1)
        #                 self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        #                 time.sleep(1)

    def page_nums_spider(self, uid):
        url = 'https://weibo.com/{}/like?page=1#feedtop'.format(uid)
        self.browser.get(url)
        self.browser.implicitly_wait(10)
        time.sleep(2)

        # while True:
        #  两次下拉，获取全部信息
        # try:
        while True:
            try:
                self.browser.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                self.browser.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                # except Exception as e:
                #     logging.warning(e)

                #  获取节点id，获取不到则没有点赞微博
                # try:
                self.browser.find_element_by_xpath(
                    '//*[@id="plc_main"]/div[2]/div[6]/div')
                self.node = self.browser.find_element_by_xpath(
                    '//*[@id="plc_main"]/div[2]/div[6]').get_attribute('id')
                break
            except Exception as e:
                logging.error(e)

        if self.node is None:
            self.node = None
            self.page_nums = None
        # except Exception as e:
        #     logging.warning(e)
        #     print("没有点赞的微博")
        #     self.node = None
        #     self.page_nums = None

        else:
            action_data = self.browser.find_element_by_xpath(
                '//*[@id="{}"]/div[2]/div[3]/div[last()]/div/span/a'.format(self.node)).get_attribute('action-data')
            if action_data is not None:
                self.page_nums = int(action_data.split('=')[2])
                self.page = 1
            else:
                if self.browser.find_element_by_xpath('//*[@id="{}"]/div[2]/div[3]/div[last()]'.format(self.node)).get_attribute('action-type') == "feed_list_item" \
                        or self.browser.find_element_by_xpath('//*[@id="{}"]/div[2]/div[3]/div[last()]/div[1]'.format(self.node)).get_attribute('action-type') == "feed_list_item":
                    self.page_nums = 1
                    self.page = 1

        if self.page_nums is not None:
            for current_page in range(1, self.page_nums + 1):
                self.page_spider(uid, current_page)

        # 爬取完某个用户后，更新状态为已爬取
        try:
            self.table.update_one(
                {'_id': uid}, {'$set': {'like_flag': 'true'}})
        except Exception as e:
            print(e)
        # return False

        # while True:
        #     #  获取点赞微博的总页数
        #     try:
        #         page_nums = self.browser.find_element_by_xpath('//*[@id="{}"]/div[2]/div[3]/div[last()]/div/span/a'.format(self.node)).get_attribute('action-data').split('=')[2]
        #         self.page_nums = int(page_nums)
        #         self.page = 1
        #         self.page_spider(uid)
        #         break
        #     #  点赞微博只有一页，则没有总页数。且最后一条微博没有被删除
        #     except Exception as e:
        #         if self.browser.find_element_by_xpath('//*[@id="{}"]/div[2]/div[3]/div[last()]'.format(self.node)).get_attribute('action-type') == "feed_list_item" \
        #                 or self.browser.find_element_by_xpath('//*[@id="{}"]/div[2]/div[3]/div[last()]/div[1]'.format(self.node)).get_attribute('action-type') == "feed_list_item":
        #             self.page_spider(uid)
        #         else:
        #             if self.count < 5:
        #                 logging.warning(e)
        #                 # self.browser.get(self.url)
        #                 # self.browser.implicitly_wait(10)
        #                 # self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        #                 # time.sleep(1)
        #                 self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        #                 self.count = self.count + 1
        #                 time.sleep(1)
        #             else:
        #                 print("加载失败!")
        #                 self.tweet_spider(uid, None)

    def page_spider(self, uid, current_page):
        # if self.page_nums is not None:
        print("pages = {}, current_page = {}".format(
            self.page_nums, current_page))
        url = 'https://weibo.com/{}/like?page={}#feedtop'.format(
            uid, current_page)
        self.browser.implicitly_wait(10)
        self.browser.get(url)
        time.sleep(2)

        while True:
            try:
                #  两次下拉，获取全部信息
                self.browser.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                self.browser.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)

                #  获取当前页的所有微博节点
                # for _ in range(1, 5):
                #     self.browser.execute_script(
                #             "window.scrollTo(0, document.body.scrollHeight)")
                tweets = self.browser.find_elements_by_xpath(
                    '//*[@id="{}"]/div[2]/div[3]/div'.format(self.node))
                break
            except Exception as e:
                logging.error(e)
        if tweets is not None:
            for tweet in tweets:
                self.tweet_spider(uid, tweet)
        # self.tweet_spider(uid, tweets)

    #  获取每一条微博的信息
    def tweet_spider(self, uid, tweet):
        try:
            if tweet.get_attribute('tbinfo'):
                text = tweet.text.split('\n')
                _id = uid + '-' + tweet.get_attribute('mid')
                user_id = uid  # 点赞用户的id
                like_id = tweet.get_attribute(
                    'tbinfo')[5:15]  # 点赞对象用户的id
                like_nick_name = text[2]  # 点赞对象用户的昵称
                content = ''.join([''.join(s.split())
                                   for s in text[3:-5]])  # 点赞微博的内容
                create_time = ''.join(
                    text[-5].split(' ')[0:2])  # 点赞微博发表时间
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
            # self.page_spider(uid)

        # #  查找一个已经爬取完微博信息的id
        # while True:
        #     user = self.table.find_one({'tweet_flag': 'true', 'like_flag': 'false'})
        #     if user is not None:
        #         uid = user['_id']
        #         print('uid:' + uid)
        #         break
        #     else:
        #         print("暂时没有可爬取的id")
        #         time.sleep(1000)
        #
        # self.page_nums_spider(uid)


if __name__ == "__main__":
    # LikesSpider().page_spider('6672809116')

    mongo_client = pymongo.MongoClient(LOCAL_MONGO_HOST, LOCAL_MONGO_PORT)
    collection = mongo_client[DB_NAME]["Likes"]
    table = mongo_client[DB_NAME]["FollowedIDs"]

    #  查找一个已经爬取完微博信息的id
    while True:
        user = table.find_one({'tweet_flag': 'true', 'like_flag': 'false'})
        if user is not None:
            uid = user['_id']
            print('uid:' + uid)
            LikesSpider(collection, table).page_nums_spider(uid)
            break
        else:
            print("暂时没有可爬取的id")
            time.sleep(1000)

    # LikesSpider('2154491277')
    # LikesSpider('2016713117')

    # url = 'https://weibo.com/5499106103/like?page=1#feedtop'
    # browser = webdriver.PhantomJS(executable_path=r'C:\phantomjs-2.1.1-windows\bin\phantomjs.exe')
    # browser.set_window_size(1050, 840)
    # browser.get(url)
    # time.sleep(3)
    # browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    # time.sleep(3)
    # browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    # time.sleep(3)
    #
    # tweets = browser.find_elements_by_xpath('//*[@id="Pl_Core_LikesFeedV6__68"]/div[2]/div[3]/div')
    # print(tweets[16].text)
    # print(tweets[23].text)
    # print(tweets[24].text)
    # print(type(tweets[2].text))
    # text = tweets[24].text.split('\n')
    # print(text)
    # nick_name = text[2]
    # print(nick_name)
    # content = ''.join(text[3:-5])
    # print(content)
    # repost_num = text[-3].split(' ')[1]
    # print(repost_num)
    # comment_num = text[-2].split(' ')[1]
    # print(comment_num)
    # like_num = text[-1]
    # print(like_num)
    # create_time = ''.join(text[-5].split(' ')[0:2])
    # print(create_time)
    #
    # next_page = browser.find_element_by_xpath('//*[@id="Pl_Core_LikesFeedV6__68"]/div[2]/div[3]/div[46]/div/a')
    # all_page = browser.find_element_by_xpath('//*[@id="Pl_Core_LikesFeedV6__68"]/div[2]/div[3]/div[46]/div/span/a')
    # print(all_page.get_attribute('action-data'))
    # print(all_page.get_attribute('action-data')[-2:])
    #
    # like_total_nums = browser.find_element_by_xpath(
    #     '//*[@id="Pl_Core_LikesFeedV6__68"]/div[2]/div[2]/div/ul/li[2]/div/span[1]')
    # print(like_total_nums.text)
    #
    # browser.close()
