# -*- coding: utf-8 -*-
from scrapy import Item, Field


class TweetsItem(Item):
    """ 原创微博信息 """
    _id = Field()  # 微博id
    weibo_url = Field()  # 微博URL
    created_at = Field()  # 微博发表时间
    like_num = Field()  # 点赞数
    repost_num = Field()  # 转发数
    comment_num = Field()  # 评论数
    content = Field()  # 微博内容
    user_id = Field()  # 发表该微博用户的id
    crawl_time = Field()  # 抓取时间戳


class InformationItem(Item):
    """ 个人信息 """
    _id = Field()  # 用户ID
    nick_name = Field()  # 昵称
    gender = Field()  # 性别
    province = Field()  # 所在省
    city = Field()  # 所在城市
    brief_introduction = Field()  # 简介
    birthday = Field()  # 生日
    tweets_num = Field()  # 微博数
    follows_num = Field()  # 关注数
    fans_num = Field()  # 粉丝数
    sex_orientation = Field()  # 性取向
    sentiment = Field()  # 感情状况
    vip_level = Field()  # 会员等级
    authentication = Field()  # 认证
    person_url = Field()  # 首页链接
    crawl_time = Field()  # 抓取时间戳
    weibo_label = Field()  # 微博标签
    learning_work_experience = Field()  # 学习和工作经历
    follow_group_label = Field()  # 关注的分组标签


class RelationshipsItem(Item):
    """ 用户关系，只保留与关注的关系 """
    _id = Field()
    fan_id = Field()  # 关注者,即粉丝的id
    followed_id = Field()  # 被关注者的id
    crawl_time = Field()  # 抓取时间戳


class FollowedIDsItem(Item):
    """ 保留所有被关注者的id """
    _id = Field()  # 被关注者的id
    tweet_flag = Field()  # 是否爬取过的标志
    like_flag = Field()  # 是否爬取过点赞的标志


class CommentItem(Item):
    """
    微博评论信息
    """
    _id = Field()
    comment_user_id = Field()  # 评论用户的id
    content = Field()  # 评论的内容
    weibo_url = Field()  # 评论的微博的url
    created_at = Field()  # 评论发表时间
    crawl_time = Field()  # 抓取时间戳


class LikesItem(Item):
    """ 微博点赞信息 """
    _id = Field()  # 点赞微博的id
    user_id = Field()  # 点赞用户的id
    like_id = Field()  # 点赞对象用户的id
    like_nick_name = Field()  # 点赞对象用户的昵称
    content = Field()  # 点赞微博的内容
    create_time = Field()  # 点赞微博发表时间
    like_num = Field()  # 点赞微博的点赞数
    repost_num = Field()  # 点赞微博的转发数
    comment_num = Field()  # 点赞微博的评论数
    crawl_time = Field()  # 抓取时间戳
    like_total_nums = Field()  # 用户赞过的微博总数
