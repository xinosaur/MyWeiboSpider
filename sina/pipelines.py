# -*- coding: utf-8 -*-
import sys
sys.path.append('/root/WeiboSpider-master/sina')
import pymongo
from pymongo.errors import DuplicateKeyError
from items import RelationshipsItem, TweetsItem, InformationItem, CommentItem, FollowedIDsItem, LikesItem
from settings import LOCAL_MONGO_HOST, LOCAL_MONGO_PORT, DB_NAME


class MongoDBPipeline(object):
    def __init__(self):
        client = pymongo.MongoClient(LOCAL_MONGO_HOST, LOCAL_MONGO_PORT)
        db = client[DB_NAME]
        self.Information = db["Information"]
        self.Tweets = db["Tweets"]
        self.Comments = db["Comments"]
        self.Relationships = db["Relationships"]
        self.FollowedIDs = db["FollowedIDs"]
        # self.Likes = db["Likes"]

    def process_item(self, item, spider):
        """ 判断item的类型，并作相应的处理，再入数据库 """
        if isinstance(item, RelationshipsItem):
            self.insert_item(self.Relationships, item)
        elif isinstance(item, TweetsItem):
            self.insert_item(self.Tweets, item)
        elif isinstance(item, InformationItem):
            self.save_item(self.Information, item)
        elif isinstance(item, CommentItem):
            self.insert_item(self.Comments, item)
        elif isinstance(item, FollowedIDsItem):
            self.insert_item(self.FollowedIDs, item)
        # elif isinstance(item, LikesItem):
        #     self.insert_item(self.Likes, item)
        return item

    @staticmethod
    def insert_item(collection, item):
        try:
            collection.insert(dict(item))
        except DuplicateKeyError:
            """
            说明有重复数据
            """
            pass

    @staticmethod
    def save_item(collection, item):
        collection.save(item)
