import pandas as pd
import numpy as np
from os import path
import json, pymongo
from . import dburi

def genelist(filename, **kwargs):
    if len(kwargs) == 0:
        grid3 = pd.read_excel(path.join("app", "uploadfiles", filename), header=0, index_col=0)
        # return [{"id": ids, "name": names} for ids, names in enumerate(np.array(grid3.index[2:]))] #用户自己导入的数据，与TCGA数据排布相反，格式改为：行为特征，列为样本
        return [{"id": ids, "name": names} for ids, names in enumerate(np.array(grid3.columns[2:]))]
    else:
        myclient = dburi.DBuri()
        mydb = myclient["cluster_record"]
        mycol = mydb["tcga_list"]
        mydoc = mycol.find_one({"type": kwargs["type"], "text":kwargs["text"]})
        return mydoc["list"]



if __name__ == '__main__':
    print(genelist("S2_data.xlsx"))