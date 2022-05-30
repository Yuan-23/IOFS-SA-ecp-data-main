import pandas as pd
from io import BytesIO
import base64

# 发邮件
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 层次聚类
import scipy.cluster.hierarchy as sch
import matplotlib
import matplotlib.pyplot as plt

from app.CoreModules.tools import load_feature_impts_from_dir
from .GMM import get_gaussian_boundary

matplotlib.use('Agg')
import time, datetime
import concurrent.futures as cf

from sklearn.model_selection import train_test_split
from app.CoreModules.Regression import extract_feature_for_acc

import numpy as np
import os
import json
from lifelines import CoxPHFitter
import asyncio
import pymongo
from . import lifescatter
from app import utilities

from flask import Flask
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from numpy.linalg import LinAlgError

executor = ThreadPoolExecutor(2)


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)


def classify_firstly(n_features, loops, uid, **kwargs):
    # 每次抽 n_features 个特征,  如 n_features = 2
    selectedlists = {}
    WORK_PATH = r'D:\iwsrahc-main'
    # Data_Path = r'D:\iwsrahc-main\app\data\microRNA\GBM.csv'
    config_dict = {"loops": loops, "n_features": n_features}

    if len(kwargs) == 0:
        # 本地上传
        datapath = os.path.join(WORK_PATH, "app", "uploadfiles", str(uid) + ".xlsx")
        data = pd.read_excel(datapath, index_col=0)
        thetype = "uploadfiles"
        asyncio.run(intodb(uid, "uploadfiles", "null", config_dict))
    else:
        # 已有
        datapath = os.path.join(WORK_PATH, "app", "data", kwargs["type"], kwargs["text"] + ".csv")
        data = pd.read_csv(datapath, index_col=0)
        thetype = kwargs["type"]
        asyncio.run(intodb(uid, kwargs["text"], kwargs["type"], config_dict))

    print(datapath)
    file_name = os.path.split(datapath)[-1].split('.')[0]

    vimps_save_dir = os.path.join(WORK_PATH, f'D:/Data/{file_name}/features{n_features}_loops{loops}_{thetype}')
    # vimps_save_dir = os.path.join(WORK_PATH, f'D:/Data/{file_name}/vimps_Survival_Cox_{n_features}_permutation')

    if not os.path.exists(vimps_save_dir):
        os.makedirs(vimps_save_dir)

    print(data.columns[:10])

    y = {'Survival state': 'vital_status', 'Survival day': 'days_to_death'}
    # y = {'Survival state': 'days_to_death', 'Survival day': 'vital_status'}

    # #去除状态和时间两列后计算评分
    # # gene_data = data.iloc[:,2:]
    # # print('*' * 8, gene_data.iloc[:5,:5])
    # data_train, data_test, _, _ = train_test_split(data, data.loc[:, y['Survival state']],
    #                                                stratify=data.loc[:, y['Survival state']],
    #                                                test_size=0.3, random_state=0)

    # 没有运行过，则异步提交任务，后台执行，并且告诉用户需等待
    if not os.listdir(vimps_save_dir):
        print("NULL")
        # executor.submit(some_long_task2, uid, data_train, y, n_features, loops, vimps_save_dir)
        executor.submit(some_long_task2, uid, data, y, n_features, loops, vimps_save_dir)
        selectedlists = {"name": "running", "id": "running"}
        print('Calculate vimps done!')

    # 已经运行过，则读取结果
    else:
        print("OKK")
        selected_name = []
        selected_id = []

        # 将计算好的特征的P值取出来，vimps从2开始取值了
        vimps = load_feature_impts_from_dir(vimps_save_dir, show=True)
        selectedlists.clear()

        # 反置，则越大越重要，argsort（a,ax）将矩阵a按照ax从小到大排序，返回排序后的下标，所以sorted_index[0]是最大值的下标
        feature_index = np.argsort(-vimps)

        # 拟合高斯来判断应该取多少特征（最后一个边界）
        vimps_gau = get_gaussian_boundary(vimps, n_components=20, show=False)

        # 最大边界的值为：vimps_max
        vimps_max = vimps_gau[-1]
        print("最大边界为：", vimps_max)
        print("边界有：", vimps_gau)

        # 大于（等于）最大边界的特征则使用
        print(data.columns)
        for i, vimp in enumerate(vimps):  # 此时的vimps已经是[2:]
            if vimp >= vimps_max:
                selected_name.append(data.columns[i + 2])  # i+2
                selected_id.append(i)
                selectedlists = {"name": selected_name, "id": selected_id}
                print(i, data.columns[i + 2], sep=':')

    return json.dumps(selectedlists, cls=MyEncoder)


# 异步提交任务，后台执行
def some_long_task2(uid, data_train, y, n_features, loops, vimps_save_dir):
    print("Task #2 is running!")

    # extract_feature_for_acc(data_train, y, n_features, loops, vimps_save_dir)
    jobs = []
    with cf.ProcessPoolExecutor(max_workers=14) as pool:
        for i in range(14):
            jobs.append(pool.submit(extract_feature_for_acc, data_train, y, n_features, loops, vimps_save_dir))
    print(len(jobs))
    asyncio.run(intodb3(uid))
    print("Task #2 is done!")


"""
genelist格式类似于[  {"Id":1,"ProductName":"香蕉","StockNum":"100","checked":true},  {"Id":3,"ProductName":"车厘子","StockNum":"2010","checked":true}]

"""


def clusterpack(genelist, uid, **kwargs):
    returndic = {}
    print("特征选择列表", genelist)
    genelist = np.array(genelist)
    genelist = genelist + 2
    if len(kwargs) == 0:
        # 本地上传
        grid3 = pd.read_excel(os.path.join("app", "uploadfiles", str(uid) + ".xlsx"), index_col=0, header=0)
        # asyncio.run(intodb(uid, "Local upload"))
    else:
        # 已有
        grid3 = pd.read_csv(os.path.join("app", "data", kwargs["type"], kwargs["text"] + ".csv"), index_col=0, header=0)
        # asyncio.run(intodb(uid, '-'.join(['TCGA', kwargs["text"], kwargs["type"], "-seq"])))
    lifespan_name = grid3.columns[1]
    censor_name = grid3.columns[0]
    grid3 = grid3.sort_values(by=lifespan_name)
    projectNames = np.array(grid3._stat_axis.values.tolist())
    projectCensors = np.array(grid3.iloc[:, 0]).reshape((1, -1))[0]
    projectLife = np.array(grid3.iloc[:, 1]).reshape((1, -1))[0]
    genelist = np.insert(genelist, 0, [0, 1])
    grid3 = grid3.iloc[:, genelist]
    # try:
    cph = CoxPHFitter(penalizer=0.1)
    # CoxPHFitter（penalizer = 0.1）.fit（...）
    # 添加惩罚器解决高共线性问题的出现
    cph.fit(grid3, duration_col=lifespan_name, event_col=censor_name)
    # except LinAlgError:
    #     print('*******************************************************')
    betalist = cph.params_
    riskscore = np.array(
        [np.sum([betaVar * grid3.iloc[line, betaItem + 2] for betaItem, betaVar in enumerate(betalist)]) for
         line in range(grid3.shape[0])])
    # riskscore = np.log(riskscore)
    # 将风险分数取对数，使热图明显(负数先绝对值再log再取负)

    i = 0
    riskscorelog = riskscore.copy()
    print("len(riskscorelog):", len(riskscorelog))
    while i < len(riskscorelog):
        if riskscorelog[i] > 0:
            # print("######riskscore[i]=", riskscorelog[i])
            riskscorelog[i] = np.log(riskscorelog[i])
        elif riskscorelog[i] == 0.:
            riskscorelog[i] = np.log(riskscorelog[i] + 1e-100)  # + 1e-100防止出现riskscore=0的情况
        else:
            riskscorelog[i] = -(np.log(abs(riskscorelog[i])))
        i = i + 1

    # i = 0
    # print("len(riskscore)", len(riskscore))
    # while i < len(riskscore):
    #     if riskscore[i] >= 0:
    #         print("######riskscore[i]=", riskscore[i])
    #         riskscore[i] = np.log(riskscore[i])  # + 1e-100防止出现riskscore=0的情况
    #     else:
    #         riskscore[i] = -(np.log(abs(riskscore[i])))
    #     i = i + 1



    print("riskscore:", riskscore)

    # riskscore = np.exp(riskscore)
    # print(riskscore)
    # riskscore_O = np.array(riskscore).reshape((1, -1))

    riskscore_T = np.array(riskscore).reshape((-1, 1))

    distmap = sch.distance.pdist(riskscore_T, metric="chebyshev")
    mergings = sch.linkage(distmap, method="complete", optimal_ordering=True)
    # leaves = sch.leaves_list(sch.optimal_leaf_ordering(mergings, distmap)).tolist()

    # mergings = sch.linkage(distmap, method="complete")
    leaves = sch.leaves_list(mergings).tolist()
    # print("org",leaves)
    asyncio.run(intodb2(uid, grid3, leaves))
    # plt.axis('off')
    plt.figure(figsize=(15, 3), dpi=80)
    plt.axis('off')
    sch.dendrogram(mergings, no_labels=True)
    picIO = BytesIO()
    plt.savefig(picIO, format='png', bbox_inches='tight', pad_inches=0.0)
    data = base64.encodebytes(picIO.getvalue()).decode()
    # print('data:image/png;base64,' + str(data))
    returndic["dendro"] = 'data:image/png;base64,' + str(data)

    returndic["score"] = list(riskscore[leaves])
    returndic["logscore"] = list(riskscorelog[leaves])

    returndic["names"] = list(projectNames[leaves])
    returndic["text"] = ['Sample name:' + returndic["names"][i] + '<br>Lifespan:' + str(list(projectLife[leaves])[i])
                         for i in range(len(returndic["names"]))]
    # returndic["censor"] = list(projectCensors[leaves])
    # returndic["life"] = list(projectLife[leaves])
    returndic["scatter"] = 'data:image/png;base64,' + str(
        lifescatter.survivalPlt(projectLife[leaves], projectCensors[leaves]))
    # print(returndic)
    return json.dumps(returndic, cls=MyEncoder)


def getfromdb(RuntimeID):
    '''
    Record of each runtime and its statues.

    :param uid: the UUID of the running environment
    :param type: embedded TCGA dataset or local machine upload
    :return: None
    '''
    myclient = utilities.dburi.DBuri()
    mydb = myclient["cluster_record"]
    mycol = mydb["log"]
    # 查询该id的数据
    myquery = {"uid": RuntimeID}
    mydoc = mycol.find(myquery)
    getdoc = {}
    for x in mydoc:
        if x["status"] == "Running":
            continue
        elif x["status"] == "Done":
            if x["type"] == "null":
                # 属于自己上传文件
                getdoc = {'uid': RuntimeID, 'text': x["input"], 'type': x["type"],
                          'loops': x["params"]["loops"], 'nums': x["params"]["n_features"],
                          'status': "Done", 'belong': "1"}
            else:
                # 属于已有文件
                getdoc = {'uid': RuntimeID, 'text': x["input"], 'type': x["type"],
                          'loops': x["params"]["loops"], 'nums': x["params"]["n_features"],
                          'status': "Done", 'belong': "2"}
            print(getdoc)

    return json.dumps(getdoc, cls=MyEncoder)


async def intodb(uid: str, text: str, type: str, params: dict) -> None:
    '''
    Record of each runtime and its statues.

    :param uid: the UUID of the running environment
    :param type: embedded TCGA dataset or local machine upload
    :return: None
    '''
    myclient = utilities.dburi.DBuri()
    mydb = myclient["cluster_record"]
    mycol = mydb["log"]
    mylog = {
        "uid": uid,
        "input": text,
        "type": type,
        "time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time())),
        "params": params,
        "status": "Running"
    }
    mycol.insert_one(mylog)


async def intodb2(uid: str, grid: pd.DataFrame, leaves: list) -> None:
    '''
    This asynic Mongodb method inserts hierarchy cluster result into
    database, in purpose to accelerate re-cluster later.

    :param uid: UUID of the runtime
    :param grid: a pandas.dataframe. stores basic sample info.
    :param leaves: permuted sample ids according to linkage result.
    :return: None.
    '''
    myclient = utilities.dburi.DBuri()
    mydb = myclient["cluster_record"]
    mycol = mydb["proc_info"]
    my_query = {"uid": uid}
    myupdate = {"$set": {"dendrolist": leaves}}
    myfind = mycol.find(my_query)
    if myfind.count() > 0:
        mycol.update_one(my_query, myupdate)
    else:
        mydict = {
            "uid": uid,
            "state": list(grid.iloc[:, 0]),
            "life": list(grid.iloc[:, 1]),
            "dendrolist": leaves
        }
        mycol.insert_one(mydict)


async def intodb3(uid: str) -> None:
    myclient = utilities.dburi.DBuri()
    mydb = myclient["cluster_record"]
    mycol = mydb["log"]
    my_query = {"uid": uid}
    myupdate = {"$set": {"status": "Done"}}
    mycol.update_one(my_query, myupdate)

# if __name__ == "__main__":
# n_features = 2
# loops = 100
# uid = 0
# #
# # selected_list = classify_firstly(n_features, loops, uid)
# # clusterpack(selected_list, uid)  # n_features, loops, uid, **kwargs
#
# classify_firstly(n_features, loops, uid)
