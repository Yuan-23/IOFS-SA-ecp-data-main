import pymongo
from . import dburi

def cancertypes():
    myclient = dburi.DBuri()
    mydb = myclient["cluster_record"]
    mycol = mydb["cancers"]
    mydoc = mycol.find_one({"version": 4})["cancer_list"]
    for items in mydoc:
        if len(items["type"]) == 0:
            items["disabled"] = 1
    # print(mydoc)
    return mydoc

if __name__ == '__main__':
    cancertypes()