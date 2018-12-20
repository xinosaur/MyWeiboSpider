#!/usr/bin/env python
# encoding: utf-8
import re

from lxml import etree
from pymongo.errors import DuplicateKeyError
from scrapy import Spider
from scrapy.crawler import CrawlerProcess
from scrapy.selector import Selector
from scrapy.http import Request
from scrapy.utils.project import get_project_settings

import sys
sys.path.append('/root/WeiboSpider-master/sina')
from items import TweetsItem, InformationItem, RelationshipsItem, CommentItem, FollowedIDsItem
from settings import LOCAL_MONGO_HOST, LOCAL_MONGO_PORT, DB_NAME
from spiders.utils import time_fix
import time

import pymongo


class WeiboSpider(Spider):
    name = "weibo_spider"
    base_url = "https://weibo.cn"

    mongo_client = pymongo.MongoClient(LOCAL_MONGO_HOST, LOCAL_MONGO_PORT)
    collection = mongo_client[DB_NAME]["FollowedIDs"]

    def start_requests(self):
        # start_uids = [
        #     # '2803301701',  # 人民日报
        #     # '2005901751',  # 北邮人论坛
        #     # '1844283341',  # 北京邮电大学
        #     # '1197755162',  # 韩雪
        #     '5499106103'
        #
        # ]
        #
        # if start_uids and start_uids[0]:
        #     for uid in start_uids:
        #         yield Request(url="https://weibo.cn/%s/info" % uid, callback=self.parse_information)

        uid = '2021115873'
        yield Request(url="https://weibo.cn/%s/info" % uid, callback=self.parse_information)
        try:
            self.collection.save({'_id': uid, 'tweet_flag': 'true', 'like_flag': 'false'})
        except DuplicateKeyError:
            pass

    # information -> further_weibo_label
    #             -> follow_group_label
    #             -> further_information -> tweet -> all_content
    #                                             -> comment
    #                                    -> fans
    #                                    -> follow
    #                                    -> like

    def parse_information(self, response):
        """ 抓取个人信息 """
        information_item = InformationItem()
        information_item['crawl_time'] = int(time.time())
        selector = Selector(response)
        information_item['_id'] = re.findall('(\d+)/info', response.url)[0]
        text1 = ";".join(selector.xpath('body/div[@class="c"]//text()').extract())  # 获取标签里的所有text()
        print(text1)
        nick_name = re.findall('昵称?[：:]?(.*?);', text1)
        gender = re.findall('性别?[：:]?(.*?);', text1)
        place = re.findall(';地区?[：:]?(.*?);', text1)
        brief_introduction = re.findall('简介[：:]?(.*?);', text1)
        birthday = re.findall('生日?[：:]?(.*?);', text1)
        sex_orientation = re.findall('性取向?[：:]?(.*?);', text1)
        sentiment = re.findall('感情状况?[：:]?(.*?);', text1)
        vip_level = re.findall('会员等级?[：:]?(.*?);', text1)
        authentication = re.findall('认证?[：:]?(.*?);', text1)
        learning_work_experience = re.findall('·(.*?)互联网', text1)

        if nick_name and nick_name[0]:
            information_item["nick_name"] = nick_name[0].replace(u"\xa0", "")
        if gender and gender[0]:
            information_item["gender"] = gender[0].replace(u"\xa0", "")

        if place and place[0]:
            place = place[0].replace(u"\xa0", "").split(" ")
            information_item["province"] = place[0]
            if len(place) > 1:
                information_item["city"] = place[1]

        if brief_introduction and brief_introduction[0]:
            information_item["brief_introduction"] = brief_introduction[0].replace(u"\xa0", "")

        if birthday and birthday[0]:
            information_item['birthday'] = birthday[0]

        if sex_orientation and sex_orientation[0]:
            if sex_orientation[0].replace(u"\xa0", "") == gender[0]:
                information_item["sex_orientation"] = "同性恋"
            else:
                information_item["sex_orientation"] = "异性恋"

        if sentiment and sentiment[0]:
            information_item["sentiment"] = sentiment[0].replace(u"\xa0", "")

        if vip_level and vip_level[0]:
            information_item["vip_level"] = vip_level[0].replace(u"\xa0", "")

        if authentication and authentication[0]:
            information_item["authentication"] = authentication[0].replace(u"\xa0", "")

        if learning_work_experience and learning_work_experience[0]:
            information_item["learning_work_experience"] = \
                learning_work_experience[0].replace(u"\xa0", " ").replace(";·", "+")[:-1]

        request_meta = response.meta
        request_meta['item'] = information_item

        # 获取用户标签
        yield Request(self.base_url + '/account/privacy/tags/?uid={}'.format(information_item['_id']),
                      callback=self.parse_weibo_label,
                      meta=request_meta, dont_filter=True, priority=1)

        # 获取用户的关注分组标签
        yield Request(url=self.base_url + '/attgroup/opening?uid={}'.format(information_item['_id']),
                      callback=self.parse_follow_group_label,
                      meta=request_meta, dont_filter=True, priority=1)

        # 获取用户的微博数、关注数、粉丝数
        yield Request(self.base_url + '/u/{}'.format(information_item['_id']),
                      callback=self.parse_further_information,
                      meta=request_meta, dont_filter=True, priority=1)

    def parse_weibo_label(self, response):
        selector = Selector(response)
        text = ";".join(selector.xpath('body/div[@class="c"]//text()').extract())  # 获取标签里的所有text()
        information_item = response.meta['item']
        weibo_label = re.findall('的标签?[：:]?(.*?)设置', text)
        if weibo_label and weibo_label[0]:
            information_item["weibo_label"] = weibo_label[0].replace(";", "").replace(u"\xa0", "+")[:-1]
        print(information_item["weibo_label"])
        yield information_item

    def parse_follow_group_label(self, response):
        selector = Selector(response)
        text = ";".join(selector.xpath('body/div[@class="c"]//text()').extract())  # 获取标签里的所有text()
        information_item = response.meta['item']
        follow_group_label = re.findall('(.*?)\]', text)
        if follow_group_label and follow_group_label[0]:
            follow_group_label[0] = ";".join(follow_group_label)
            information_item["follow_group_label"] = \
                follow_group_label[0].replace(";;", "]+").replace(u"\xa0;", "") + "]"

    def parse_further_information(self, response):
        text = response.text
        information_item = response.meta['item']
        tweets_num = re.findall('微博\[(\d+)\]', text)
        if tweets_num:
            information_item['tweets_num'] = int(tweets_num[0])
        follows_num = re.findall('关注\[(\d+)\]', text)
        if follows_num:
            information_item['follows_num'] = int(follows_num[0])
        fans_num = re.findall('粉丝\[(\d+)\]', text)
        if fans_num:
            information_item['fans_num'] = int(fans_num[0])

        # 获取粉丝列表
        yield Request(url=self.base_url + '/{}/fans?page=1'.format(information_item['_id']),
                      callback=self.parse_fans,
                      dont_filter=True)

        # 获取关注列表
        yield Request(url=self.base_url + '/{}/follow?page=1'.format(information_item['_id']),
                      callback=self.parse_follow,
                      dont_filter=True)
        #
        # 获取该用户的所有微博
        yield Request(url=self.base_url + '/{}/profile?page=1'.format(information_item['_id']),
                      callback=self.parse_tweet,
                      priority=1)


    def parse_tweet(self, response):
        if response.url.endswith('page=1'):
            # 如果是第1页，一次性获取后面的所有页
            all_page = re.search(r'/>&nbsp;1/(\d+)页</div>', response.text)
            if all_page:
                all_page = all_page.group(1)
                all_page = int(all_page)
                for page_num in range(2, all_page + 1):
                    page_url = response.url.replace('page=1', 'page={}'.format(page_num))
                    yield Request(page_url, self.parse_tweet, dont_filter=True, meta=response.meta)
        """
        解析本页的数据
        """
        all_page = re.search(r'/>&nbsp;(\d+)/(\d+)页</div>', response.text)

        tree_node = etree.HTML(response.body)
        tweet_nodes = tree_node.xpath('//div[@class="c" and @id]')
        for tweet_node in tweet_nodes:
            try:
                tweet_item = TweetsItem()
                tweet_item['crawl_time'] = int(time.time())
                tweet_repost_url = tweet_node.xpath('.//a[contains(text(),"转发[")]/@href')[0]
                user_tweet_id = re.search(r'/repost/(.*?)\?uid=(\d+)', tweet_repost_url)
                tweet_item['weibo_url'] = 'https://weibo.com/{}/{}'.format(user_tweet_id.group(2),
                                                                           user_tweet_id.group(1))
                tweet_item['user_id'] = user_tweet_id.group(2)
                tweet_item['_id'] = '{}_{}'.format(user_tweet_id.group(2), user_tweet_id.group(1))
                create_time_info = tweet_node.xpath('.//span[@class="ct" and contains(text(),"来自")]/text()')[0]
                tweet_item['created_at'] = time_fix(create_time_info.split('来自')[0].strip())

                like_num = tweet_node.xpath('.//a[contains(text(),"赞[")]/text()')[-1]
                tweet_item['like_num'] = int(re.search('\d+', like_num).group())

                repost_num = tweet_node.xpath('.//a[contains(text(),"转发[")]/text()')[-1]
                tweet_item['repost_num'] = int(re.search('\d+', repost_num).group())

                comment_num = tweet_node.xpath(
                    './/a[contains(text(),"评论[") and not(contains(text(),"原文"))]/text()')[-1]
                tweet_item['comment_num'] = int(re.search('\d+', comment_num).group())

                tweet_repost_node = tweet_node.xpath('.//span[@class="ctt"]')[0]
                tweet_original_node = tweet_node.xpath('.//span[@class="cmt"]')

                # 检测由没有阅读全文:
                all_content_link = tweet_repost_node.xpath('.//a[text()="全文"]')

                # 如果是原创微博，只有ctt
                # 如果是转发微博，ctt是转发微博的内容，cmt是转发理由
                if tweet_original_node:
                    repost_contemt = tweet_original_node[0].xpath('string(.)').strip().replace(u"\xa0", " ") + \
                                     tweet_repost_node.xpath('string(.)').replace('\u200b', '').replace('\u2028', '').strip()
                    content = re.findall('(.*?)//',
                                         re.findall(r'转发理由:(.*?)赞', tweet_node.xpath('string(.)'))[0]
                                         .replace('\u2028', '').strip())
                    if content:
                        original_content = "转发理由：" + content[0]
                    else:
                        original_content = "转发理由：" + \
                                           re.findall(r'转发理由:(.*?)赞', tweet_node.xpath('string(.)'))[0]\
                                               .replace('\u2028', '').strip()
                    tweet_item['content'] = repost_contemt + "+" + original_content
                    yield tweet_item
                else:
                    if all_content_link:
                        all_content_url = self.base_url + all_content_link[0].xpath('./@href')[0]
                        yield Request(all_content_url, callback=self.parse_all_content, meta={'item': tweet_item},
                                      priority=1)
                    else:
                        all_content = tweet_repost_node.xpath('string(.)').replace('\u200b', '')\
                            .replace('\u2028', '').strip()
                        tweet_item['content'] = all_content
                        yield tweet_item

                # tweet_content_node = tweet_node.xpath('.//span[@class="ctt"]')[0]

                # 检测由没有阅读全文:
                # all_content_link = tweet_content_node.xpath('.//a[text()="全文"]')
                # if all_content_link:
                #     all_content_url = self.base_url + all_content_link[0].xpath('./@href')[0]
                #     yield Request(all_content_url, callback=self.parse_all_content, meta={'item': tweet_item},
                #                   priority=1)
                #
                # else:
                #     all_content = tweet_content_node.xpath('string(.)').replace('\u200b', '').strip()
                #     tweet_item['content'] = all_content
                #     # yield tweet_item
                #     print(tweet_item)

                # 抓取该微博的评论信息
                # comment_url = self.base_url + '/comment/' + tweet_item['weibo_url'].split('/')[-1] + '?page=1'
                # yield Request(url=comment_url, callback=self.parse_comment,
                #               meta={'weibo_url': tweet_item['weibo_url']})

            except Exception as e:
                self.logger.error(e)

        if all_page:
            if response.url.endswith(all_page.group(2)):
                while True:
                    user = self.collection.find_one({'tweet_flag': 'false'})
                    if user is not None:
                        uid = user['_id']
                        yield Request(url="https://weibo.cn/%s/info" % uid, callback=self.parse_information)
                        self.collection.update_one({'_id': uid}, {'$set': {'tweet_flag': 'true'}})
                        break
                    else:
                        print("暂时没有可爬取的id")
                        time.sleep(10)
        else:
            while True:
                user = self.collection.find_one({'tweet_flag': 'false'})
                if user is not None:
                    uid = user['_id']
                    yield Request(url="https://weibo.cn/%s/info" % uid, callback=self.parse_information)
                    self.collection.update_one({'_id': uid}, {'$set': {'tweet_flag': 'true'}})
                    break
                else:
                    print("暂时没有可爬取的id")
                    time.sleep(10)

    def parse_all_content(self, response):
        # 有阅读全文的情况，获取全文
        tree_node = etree.HTML(response.body)
        tweet_item = response.meta['item']
        content_node = tree_node.xpath('//div[@id="M_"]//span[@class="ctt"]')[0]
        all_content = content_node.xpath('string(.)').replace('\u200b', '').replace('\u2028', '').strip()
        tweet_item['content'] = all_content
        yield tweet_item

    def parse_comment(self, response):
        # 如果是第1页，一次性获取后面的所有页
        if response.url.endswith('page=1'):
            all_page = re.search(r'/>&nbsp;1/(\d+)页</div>', response.text)
            if all_page:
                all_page = all_page.group(1)
                all_page = int(all_page)
                for page_num in range(2, all_page + 1):
                    page_url = response.url.replace('page=1', 'page={}'.format(page_num))
                    yield Request(page_url, self.parse_comment,
                                  dont_filter=True, meta=response.meta)
        selector = Selector(response)
        comment_nodes = selector.xpath('//div[@class="c" and contains(@id,"C_")]')
        for comment_node in comment_nodes:
            comment_user_url = comment_node.xpath('.//a[contains(@href,"/u/")]/@href').extract_first()
            if not comment_user_url:
                continue
            comment_item = CommentItem()
            comment_item['crawl_time'] = int(time.time())
            comment_item['weibo_url'] = response.meta['weibo_url']
            comment_item['comment_user_id'] = re.search(r'/u/(\d+)', comment_user_url).group(1)
            comment_item['content'] = comment_node.xpath('.//span[@class="ctt"]').xpath('string(.)').extract_first()
            comment_item['_id'] = comment_node.xpath('./@id').extract_first()
            created_at = comment_node.xpath('.//span[@class="ct"]/text()').extract_first()
            comment_item['created_at'] = time_fix(created_at.split('\xa0')[0])
            yield comment_item

    def parse_fans(self, response):
        """
        抓取粉丝列表
        """
        # 如果是第1页，一次性获取后面的所有页
        if response.url.endswith('page=1'):
            all_page = re.search(r'/>&nbsp;1/(\d+)页</div>', response.text)
            if all_page:
                all_page = all_page.group(1)
                all_page = int(all_page)
                for page_num in range(2, all_page + 1):
                    page_url = response.url.replace('page=1', 'page={}'.format(page_num))
                    yield Request(page_url, self.parse_fans,
                                  dont_filter=True, meta=response.meta)
        selector = Selector(response)
        urls = selector.xpath('//a[text()="关注他" or text()="关注她" or text()="移除"]/@href').extract()
        uids = re.findall('uid=(\d+)', ";".join(urls), re.S)
        ID = re.findall('(\d+)/fans', response.url)[0]
        for uid in uids:
            relationships_item = RelationshipsItem()
            relationships_item['crawl_time'] = int(time.time())
            relationships_item["fan_id"] = uid
            relationships_item["followed_id"] = ID
            relationships_item["_id"] = uid + '-' + ID
            yield relationships_item

    def parse_follow(self, response):
        """
        抓取关注列表
        """
        # 如果是第1页，一次性获取后面的所有页
        if response.url.endswith('page=1'):
            all_page = re.search(r'/>&nbsp;1/(\d+)页</div>', response.text)
            if all_page:
                all_page = all_page.group(1)
                all_page = int(all_page)
                for page_num in range(2, all_page + 1):
                    page_url = response.url.replace('page=1', 'page={}'.format(page_num))
                    yield Request(page_url, self.parse_follow,
                                  dont_filter=True, meta=response.meta)
        selector = Selector(response)
        urls = selector.xpath('//a[text()="关注他" or text()="关注她" or text()="取消关注"]/@href').extract()
        uids = re.findall('uid=(\d+)', ";".join(urls), re.S)
        ID = re.findall('(\d+)/follow', response.url)[0]
        for uid in uids:
            relationships_item = RelationshipsItem()
            relationships_item['crawl_time'] = int(time.time())
            relationships_item["fan_id"] = ID
            relationships_item["followed_id"] = uid
            relationships_item["_id"] = ID + '-' + uid
            yield relationships_item

            followedIDs_item = FollowedIDsItem()
            followedIDs_item['_id'] = uid
            followedIDs_item['tweet_flag'] = 'false'
            followedIDs_item['like_flag'] = 'false'
            yield followedIDs_item


if __name__ == "__main__":
    process = CrawlerProcess(get_project_settings())
    process.crawl(WeiboSpider)
    process.start()
