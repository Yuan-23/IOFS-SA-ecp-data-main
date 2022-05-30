# import pandas as pd
# import scipy
# import scipy.cluster.hierarchy as sch
import copy
import base64
#图
from lifelines import KaplanMeierFitter
from lifelines.plotting import add_at_risk_counts

from lifelines.statistics import logrank_test
import pymongo
from io import BytesIO
import json
import asyncio
#层次聚类
from scipy.cluster.hierarchy import dendrogram, linkage
from matplotlib import pyplot as plt
# from matplotlib import cm
# plt.set_cmap(cmap="Set2")
import numpy as np
from app import utilities

# grid3 = pd.read_excel("../uploadfiles/target.xlsx", index_col=0, header=0)
# print(grid3.iloc[:,[0]].values)
# grid3 = grid3.sort_values(by="Survival day")
# cph = CoxPHFitter()
# cph.fit(grid3, duration_col="Survival day", event_col="Survival state")
# betalist = cph.params_
# riskscore = [np.sum([betaVar*grid3.iloc[line, betaItem+2] for betaItem, betaVar in enumerate(betalist)]) for line in range(grid3.shape[0])]
# riskscore_O = np.array(riskscore).reshape((1, -1))
# riskscore_T = np.array(riskscore).reshape((-1, 1))
#
# distmap = sch.distance.pdist(riskscore_T, metric="euclidean")
# mergings = sch.linkage(distmap, method="ward")
# # sch.dendrogram(mergings)
# dendrolist = sch.leaves_list(mergings).tolist()
# print(sch.leaves_list(mergings).tolist())
# targetBoundery = [60,87,125,243]
'''
this is the Core re-hierarchy module. Its main target is to 
generate Grouped K-M graph. this above is just for debug. for
industry environment, this module is called by the main process.
'''
clinic = {}


class Subjects(object):
    """
    This class is the universal identifier for logrank-test based
    re-hierarchy cluster method.
    - Use this to recognize a **GROUP**
    """
    global clinic
    id_name = 0

    def __init__(self):
        """
        :field id: Original and newly generated id of each Subject object
        :field group: the specified id of sample in the original dataset
        """
        self.id = None
        self.name = None
        self.lchild = None
        self.rchild = None
        # 记录每次合并的左右 边界点
        self.lnum = None
        self.rnum = None
        self.genes = None
        self.state = None
        self.life = None
        self.groups = None
        self.count = 0

    def createnode(self, grouped, ids):
        self.id = str(ids)
        self.name = ids
        self.lnum = ids
        self.rnum = ids
        self.groups = grouped
        self.state = np.array(clinic["state"])[grouped]
        self.life = np.array(clinic["life"])[grouped]
        self.count = 1
        return self

    def __str__(self):
        return str(self.name)



class rehierachy_cluster(object):
    global clinic

    def __init__(self, nodedict):
        self.orgdict = nodedict
        self.matlist = None
        self.linkmat = []
        self.dictkey = len(nodedict)

        self.donedict = None
        self.finmat = None
        self.donecluster = 0

    def __combinenode(self, subject1: Subjects, subject2: Subjects, pvar: int):
        newnode = Subjects()
        newnode.count = subject1.count + subject2.count
        newnode.id = subject1.id + "+" + subject2.id
        # 将每个节点的左右合成边界记录下来
        newnode.lnum = min(subject1.lnum, subject2.lnum)
        newnode.rnum = max(subject1.rnum, subject2.rnum)
        newnode.name = Subjects.id_name
        Subjects.id_name += 1
        newnode.groups = subject1.groups + subject2.groups
        newnode.state = np.array(clinic["state"])[newnode.groups]
        newnode.life = np.array(clinic["life"])[newnode.groups]
        self.linkmat.append([subject1.name, subject2.name, 1 - pvar, newnode.count])
        newnode.lchild = copy.deepcopy(subject1)
        newnode.rchild = copy.deepcopy(subject2)
        return newnode

    def __logrank_pmat(self, **kwargs):
        pmat = list()
        for i in self.orgdict.keys():
            for j in self.orgdict.keys():
                if self.orgdict[i].lnum == self.orgdict[j].rnum + 1:
                    pmat.append({
                        "pvar": logrank_test(
                            self.orgdict[i].life,
                            self.orgdict[j].life,
                            self.orgdict[i].state,
                            self.orgdict[j].state
                        ).p_value,
                        "key1": i,
                        "key2": j,
                        "count": self.orgdict[i].count + self.orgdict[j].count
                    })
                else:
                    pass

        self.matlist = pmat
        # ! the following part only works for pure value dist matrix.
        # ! Current method uses dict list.
        # if kwargs["dist"] == "square":
        # return square form distance matrix
        # return scipy.spatial.distance.squareform(pmat)
        # return condensed distance matrix(vector) by default.
        # return np.array(pmat)

    def rehierachy_cluster(self, **kwargs):
        self.__logrank_pmat()
        self.sortinglist()
        if len(kwargs) == 2:
            """
            Two params: p-value and merging times. Cluster procedure will stop once this two params
                reached to the limit.
            - this method is currently uncallable.
            """
            layer = kwargs["layer"]
            pvar = kwargs["pvar"]
        elif len(kwargs) == 1:
            '''
            Only one param: p-value. merging will stop until no more groups matching the p-value rule.
            '''
            pvar = kwargs["pvar"]
            while True:
                self.sortinglist()
                print(self.matlist[0])
                if self.matlist[0]["pvar"] <= pvar and self.donecluster == 0:
                    # the furthest group could not get combined.
                    self.finmat = copy.deepcopy(self.matlist)
                    # matlist is for revealing p-value
                    self.donedict = copy.deepcopy(self.orgdict)
                    # orgdict contains sample info in a group (draw K-M)
                    print(self.donedict)
                    self.donecluster = 1
                elif len(self.matlist) == 1:
                    # the last branch of dendrogram
                    if self.donecluster == 0:
                        self.finmat = copy.deepcopy(self.matlist)
                        self.donedict = copy.deepcopy(self.orgdict)
                    self.linkmat.append([self.matlist[0]["key1"], self.matlist[0]["key2"],
                                         1 - self.matlist[0]["pvar"], self.matlist[0]["count"]])
                    break
                else:
                    # combining nodes. normal circumstances.
                    self.orgdict[self.dictkey] = self.__combinenode(
                        self.orgdict[self.matlist[0]["key1"]],
                        self.orgdict[self.matlist[0]["key2"]],
                        self.matlist[0]["pvar"]
                    )
                    del self.orgdict[self.matlist[0]["key1"]]
                    del self.orgdict[self.matlist[0]["key2"]]
                    self.matlist.pop(0)
                    self.__logrank_pmat()
                    self.dictkey += 1
        else:
            raise Exception("Wrong number of params!")

    def sortinglist(self):
        self.matlist = sorted(self.matlist, key=lambda i: i["pvar"], reverse=True)
        # default: asc, reverse=True desc

    def getcombinedgroups(self):
        # return self.orgdict
        return self.donedict

    def getpmat(self):
        # this method is only meaningful when the clustering is done.
        # It's main purpose is to add annotations on K-M curve.
        # return self.matlist
        return self.finmat

    def getlinkmat(self):
        return self.linkmat


def splitgroups(bounderies: list, dendrolist: list) -> dict:
    """
    Function
        Split all subjects into groups using given boundary values.

    :param bounderies: the boudary to split given dataset.
    :param dendrolist: all leaves of the hiearchy cluster dendrogram.
    :return:
        Grouped subjects. each dict value is a Subjects object.
    """
    groupcount = 0
    grouptotal = len(bounderies) + 1
    grouped = {
        k: [] for k in range(grouptotal)
    }
    for item_iter, items in enumerate(dendrolist):
        if item_iter in bounderies:
            groupcount += 1
        grouped[groupcount].append(items)
    Subjects.id_name = grouptotal
    return {
        keys: Subjects().createnode(values, keys) for keys, values in grouped.items()
    }


def export_rehier(uid: str, bounderies: list, pvalue: int) -> str:
    """
    For outside call, this method is the entrance of entire
    log-rank test based re-hierarchy cluster.

    :param uid: the runtime uuid.
    :param bounderies: user defined split bouderies on the Web panel.
    :return:
        json string for web client. including new K-M curve.
    """
    global clinic
    clinic.clear()
    myclient = utilities.dburi.DBuri()
    mydb = myclient["cluster_record"]
    mycol = mydb["proc_info"]
    mydoc = mycol.find_one({"uid": uid})
    clinic = mydoc
    grouped = splitgroups(bounderies, mydoc["dendrolist"])
    combined = rehierachy_cluster(grouped)
    combined.rehierachy_cluster(pvar=pvalue)
    print("#############P=", pvalue)
    combinedd = combined.getcombinedgroups()
    print(combinedd)
    # print(combined.getpmat())
    # print(combined.getlinkmat())
    figure2 = plt.figure(figsize=(10, 5))
    ax_new = figure2.add_subplot(121)
    ax2 = figure2.add_subplot(122)

    # fig = plt.figure()
    # ax = fig.addplot()
    kmflist = []
    for key in combinedd:
        kmf = KaplanMeierFitter()
        # print(combinedd[key].life)
        ax_new = kmf.fit(combinedd[key].life, combinedd[key].state,
                         label="group:" + str(combinedd[key].id)).plot_survival_function(ax=ax_new,
                                                                                         show_censors=True,
                                                                                         ci_show=False)
        kmflist.append(kmf)
    ax_new.text(0, 0.1, "$P_{logrank} =$ %.4g" % combined.getpmat()[0]["pvar"],fontsize=13)
    ax_new.set_title("\nKaplan-Meier Survival Curve\n")
    ax_new.set_xlabel("Survival time")
    ax_new.set_ylabel("Survival proportion")
    ax_new.grid(True, linestyle="-.")
    ax_new.spines["top"].set_visible(False)
    ax_new.spines["right"].set_visible(False)
    # for kmfs in kmflist:
    add_at_risk_counts(*kmflist, ax=ax_new)
    # mapt = sns.clustermap(riskscore_O, cmap="plasma", method="ward", metric="euclidean", col_cluster=True, row_cluster=False, figsize=(15, 5), xticklabels=True)
    # plt.show()
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.set_title("\nRe-hierarchical Clustering Tree\n")
    ax2.set_xlabel("Dissimilarity")
    ax2.set_ylabel("Sub-group ID")
    print(combined.getlinkmat())
    dendrogram(np.array(combined.getlinkmat()), ax=ax2, orientation='right',
               color_threshold=1-combined.getpmat()[0]["pvar"],
               above_threshold_color='#dcdccd')
    picIO = BytesIO()

    figure2.savefig(picIO, format='png', bbox_inches='tight', pad_inches=0.0)
    # plt.show()
    # asyncio.run(intodb(uid))
    # return json.dumps({"KMcurve": 'data:image/svg+xml;base64,' + str(base64.encodebytes(picIO.getvalue()).decode())})
    return json.dumps({"KMcurve": 'data:image/png;base64,' + str(base64.encodebytes(picIO.getvalue()).decode())})




# print(logrank_test(grouped[1].iloc[:, 1], grouped[0].iloc[:, 1], grouped[1].iloc[:, 0], grouped[0].iloc[:, 0]).p_value)
# print(logrank_pmat(grouped))
# print(mapt.dendrogram_col.dendrogram["leaves"])
# plt.show()
if __name__ == '__main__':
    export_rehier("Ujlj3vv5", [224])
