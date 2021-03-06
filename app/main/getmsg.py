#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-07-14 10:20:40
# @Author  : Wangmengcn (eclipse_sv@163.com)
# @Link    : https://eclipsesv.com
# @Version : $0.1$
# this is for getting message from redis subscribe and send it to socketio
# server
from pymongo import MongoClient
import redis
import pymongo
from datetime import datetime


# 从数据库中获取关于直播间更为详细信息
client = MongoClient()
db = client["Douyu"]
roomcol = db["Roominfo"]
col = db['rocket']


# 获取所有直播分类


def getAllTags():
    '''
    返回所有直播分类
    '''
    tagcol = db['kindRecord']
    tags = tagcol.distinct('tag')
    if tags:
        return tags
    else:
        return None


def getOnline():
    '''
    获取当前所有类别的在线情况
    '''
    onlineCol = db['Roominfo']
    sortbyKind = [{"$project": {'audience': 1, 'tag': 1, 'date': 1}}, {
        "$group": {"_id": '$tag', "sum": {"$sum": '$audience'}}}]
    onlineinfo = onlineCol.aggregate(sortbyKind)
    result = [{'tag': item['_id'], 'online':item['sum']}
              for item in onlineinfo]
    return result if result else None


def getTaginfo(tag):
    '''
    获取指定类别直播人数和该分类下所有主播
    '''
    if tag:
        taginfo = db['kindRecord']
        result = taginfo.find({'tag': tag}, {'_id': 0, 'date': 0}).sort(
            'date', pymongo.DESCENDING).limit(1)
        taganchor = db['Roominfo']
        anchors = taganchor.find(
            {'tag': tag}, {'_id': 0, 'img': 0, 'date': 0, 'tag': 0})
        if anchors.count() != 0:
            anchorsinfo = [{'anchor': item['anchor'], 'audience':item['audience'], 'roomid':item[
                'roomid'], 'roomtitle':item['roomtitle']} for item in anchors]
            if result.count() != 0:
                return result[0], anchorsinfo
            else:
                return None
        else:
            return None


def getAnchors():
    '''
    获取所有主播
    '''
    anchors = db['Roominfo']
    anchordata = anchors.find({}, {'_id': 0, 'img': 0, 'date': 0}).sort('audience',pymongo.DESCENDING)
    if anchordata.count() != 0:
        anchorsinfo = [{'anchor': item['anchor'], 'audience':item['audience'], 'roomid':item[
            'roomid'], 'roomtitle':item['roomtitle'], 'tag':item['tag']} for item in anchordata]
        return anchorsinfo
    else:
        return None


def getAnchorinfo(anchor):
    '''
    获取指定主播的人气随时间变化情况
    '''
    if anchor:
        anchorcol = db['anchorRecord']
        anchorinfo = anchorcol.find({'anchor':anchor}).sort('date',pymongo.ASCENDING)
        if anchorinfo.count() != 0:
            result = [{'anchor': item['anchor'], 'audience':item['audience'], 'tag':item['tag'],'date':str(item['date'])} for item in anchorinfo]
            return result
        else:
            return None

# 当前可以抢鱼丸的房间


def RocketRoom(roomid):
    if roomid:
        room = roomcol.find_one({"roomid": roomid}, {"_id": 0, "date": 0})
        if room:
            return room
        else:
            return None

# 按照观众人数，前20名房间


def HotRoom():
    hotroom = roomcol.find({}, {"_id": 0, "date": 0}).sort(
        "audience", pymongo.DESCENDING).limit(21)
    rooms = []
    if hotroom:
        for item in hotroom:
            rooms.append(item)
    return rooms

# 按照输入date，查询当天逐小时鱼丸分布状态


def sortbyDay(date):
    if isinstance(date, datetime):
        year = date.year
        m = date.month
        d = date.day
        singledate = datetime(year, m, d)
        print singledate
        singledata = []
        count = 0
        hour = range(0, 24)
        for h in hour:
            data = []
            value = {}
            start = datetime(year, m, d, h, 0, 0)
            end = datetime(year, m, d, h, 59, 59)
            daydata = col.find(
                {'date': {'$gt': start, '$lt': end}}, {'_id': 0})
            if daydata is not None:
                for item in daydata:
                    data.append(item)
                    count = count + 1
            else:
                data = None
            value['hour'] = h
            value['rockets'] = data
            singledata.append(value)
        if count != 0:
            insertdata = {
                'date': singledate,
                'data': singledata,
                'count': count
            }
            return insertdata
        else:
            return None


def sortNames(data, key, rank):
    sortdata = rank
    for rocket in data:
        senderkey = rocket[key].encode('utf-8')
        if senderkey not in sortdata.keys():
            sortdata[senderkey] = 1
        else:
            sortdata[senderkey] += 1
    return sortdata

# 向外提供数据，每日火箭总数、每小时火箭数量、发送者和接收者排名


def valuebyHour(date):
    daydata = sortbyDay(date)
    count = 0
    hourvalue = []
    sendervalue = {}
    recvervalue = {}
    if daydata is not None:
        count = daydata['count']
        hourdata = daydata['data']
        for h in hourdata:
            hourvalue.append(len(h['rockets']))
            sender = 'sender_id'
            recver = 'recver_id'
            rocket = h['rockets']
            if len(rocket) != 0:
                sendervalue = sortNames(rocket, sender, sendervalue)
                recvervalue = sortNames(rocket, recver, recvervalue)
        return (count, hourvalue, sendervalue, recvervalue)
    else:
        return None


# 用于获取弹幕信息和火箭信息的redis 订阅频道
redis = redis.StrictRedis(password='abc@123')
chatcast = redis.pubsub()
chatcast.subscribe('chatinfo')

rocketcast = redis.pubsub()
rocketcast.subscribe('rocketinfo')
