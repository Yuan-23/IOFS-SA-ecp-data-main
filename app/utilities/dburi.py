import pymongo


def DBuri():
    return pymongo.MongoClient("mongodb://127.0.0.1:27017/")