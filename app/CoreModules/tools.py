import numpy as np
import matplotlib
# matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import os, time, math
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.mixture import GaussianMixture
# from Classify import Classifier
from scipy import cluster

from app.CoreModules.Classify import Classifier


def load_data(data_path):
    if os.path.splitext(data_path)[-1] == '.npy':
        data = np.load(data_path)
        label = data[:, -1]
        label = np.where(label == 1, 1, 0)
        data = data[:, :-1]

    elif os.path.splitext(data_path)[-1] == '.csv':
        data = pd.read_csv(data_path)
        label = np.where(data['class'] == 'p', 1, 0)
        data = data.iloc[:, :-1].values
    else:
        raise TypeError
    return data, label


def load_feature_impts_from_dir(file_dir=r'save_vimps', show=False):
    '''
    导入基因重要性特征
    '''
    file_list = os.listdir(file_dir)
    for i, file in enumerate(file_list):
        file_path = os.path.join(file_dir, file)
        if i == 0:
            data = np.load(file_path)
        else:
            data += np.load(file_path)

    plt.plot(np.arange(data.shape[0]), data[:, 1], '.k')
    plt.xlabel('Feature Index')
    plt.ylabel('Checked feature Count')
    plt.title('Feature Count')
    plt.show()

    # plt.hist(data[:,1])
    # plt.show()

    vimps = data[:, 0] / data[:, 1]  # 得分，越小越重要

    zeros_index = np.where(data[:, 1] == 0)[0]
    if len(zeros_index) != 0:
        vimps[zeros_index] = 1345


    if show == True:
        plt.plot(np.arange(data.shape[0]), vimps, '.k')
        sorted_index = np.argsort(-vimps)  # 反置，则越大越重要，argsort（a,ax）将矩阵a按照ax从小到大排序，返回排序后的下标
        for i in range(30):
            plt.text(sorted_index[i], vimps[sorted_index[i]], str(sorted_index[i]))
        plt.title(file_dir[33:])
        plt.xlabel('feature idx')
        plt.ylabel('feature score')
        # plt.ylim([0,0.25])
        plt.show()
        # print(sorted_index[:20])
    return vimps[2:]


def load_and_show_feature_std(vimps, file_dir=r'save_svimps'):
    file_list = os.listdir(file_dir)
    for i, file in enumerate(file_list):
        file_path = os.path.join(file_dir, file)
        if i == 0:
            t = np.load(file_path)
            data = np.zeros([len(file_list), t.shape[0]])
            data[i, :] = t[:, 0] / t[:, 1]
        else:
            t = np.load(file_path)
            data[i, :] = t[:, 0] / t[:, 1]

    std = data.std(axis=0)
    plt.plot(data.std(axis=0), '.k')
    plt.title('std')
    plt.show()

    index = np.where(vimps > 0.005)[0]
    index = np.where(std > 0.01)[0]
    plt.boxplot(data[:, index], showmeans=True)

    plt.xticks(range(1, len(index) + 1), index)
    plt.show()

    # for i in np.where(std > 0.02)[0]:
    #     plt.plot(data[:, i],'.', label=str(i))
    # plt.legend()
    # plt.plot(data[:, 14],'.k')
    # plt.show()
    return std


def get_best_base_clfs(X, y):
    '''
        将输入数据X,y， 按照7：3分为训练集和测试集，使用训练集来训练所有的分类器，使用测试集找出得分最高的分类器
        input: X, y
        return best_clf
    '''
    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.3, stratify=y, random_state=None)
    classifier = Classifier()
    classifier = classifier.fit(x_train, y_train)
    classifier.find_best_ensembles(x_test, y_test, accuracy=False)
    return classifier.best_clf


class Vimps:
    '''
        计算特征重要性时，用来记录每次抽取的特征重要性

        一个简单的数据结构
    '''

    def __init__(self, num_of_features, save_dir=None):
        self.vimps = np.zeros(num_of_features, )
        self.count_feature = np.zeros(num_of_features, )
        self.save_dir = save_dir
        self.__check()

    def __check(self):
        if self.save_dir != None and not os.path.isdir(self.save_dir):
            raise Exception(f'This dir {self.save_dir} is not exist.')

    def update(self, n_feature_vimps):
        if isinstance(n_feature_vimps, dict):
            for key, value in n_feature_vimps.items():
                self.vimps[key] += value
                self.count_feature[key] += 1
        elif isinstance(n_feature_vimps, np.ndarray):
            self.vimps += n_feature_vimps
            self.count_feature += 1

    def get_avg_vimps(self):
        not_nan_idx = np.where(self.count_feature != 0)
        return self.vimps[not_nan_idx] / self.count_feature[not_nan_idx]

    def save_vimps(self, save_path=None):
        if self.save_dir != None and save_path == None:
            save_path = os.path.join(self.save_dir, f'vimps_and_count_{time.time()}.npy')
        elif self.save_dir == None and save_path == None:
            save_path = f'vimps_and_count_{time.time()}.npy'
        elif self.save_dir != None and save_path != None:
            save_path = os.path.join(self.save_dir, save_path)
        print("#################")
        np.save(save_path, np.hstack([self.vimps.reshape(-1, 1),
                                      self.count_feature.reshape(-1, 1)]))
        print("%%%%%%%%%%%%%%%")


def split_gaussian(Weight1, Weight2, Miu1, Miu2, delta1, delta2):
    """
        通过高斯密度函数计算两个高斯之间的交点
    """
    if not (delta1 and delta2):
        return (Miu1 + Miu2) / 2
    A = 1 / (delta1 ** 2) - 1 / (delta2 ** 2)
    B = -2 * (Miu1 / delta1 ** 2 - Miu2 / delta2 ** 2)
    C = Miu1 ** 2 / delta1 ** 2 - Miu2 ** 2 / delta2 ** 2 - 2 * math.log((Weight1 * delta2) / (Weight2 * delta1))
    x1 = (-B + (B ** 2 - 4 * A * C) ** 0.5) / (2 * A)
    x2 = (-B - (B ** 2 - 4 * A * C) ** 0.5) / (2 * A)
    if x1 < max(Miu1, Miu2) and x1 > min(Miu1, Miu2):
        return x1
    elif x2 < max(Miu1, Miu2) and x2 > min(Miu1, Miu2):
        return x2
    else:
        print('两正态分布之间无交点')
    return 0


def showfigure(weights, means, covars, data_vector, gaussian_boundary):
    x_max = max(data_vector)
    x_min = min(data_vector)
    for i, (w, m, c) in enumerate(zip(weights, means, covars)):
        x = np.arange(min(data_vector), max(data_vector), 0.001)
        # else:
        #     x = np.arange(0.004, 0.1, 0.0001)
        y = []
        for j in x:
            y.append(w * _gaussian(j, m, c))

        plt.plot(x, y, '--r')
    # plt.hist(data_vector,bins=50,color='r',alpha=0.4)
    for x in gaussian_boundary:
        plt.plot([x, x], [0, 20], 'b')
    plt.plot(data_vector, np.zeros(data_vector.shape), '.k', markersize=8)
    plt.ylabel('Density')
    # plt.xlabel('Feature Index')
    # plt.xlabel('Accumulated importance')
    plt.tick_params(labelsize=18)
    plt.show()


def _gaussian(x, mean, covar):
    left = 1 / (math.sqrt(2 * math.pi) * covar)
    right = math.exp(-math.pow(x - mean, 2) / (2 * math.pow(covar, 2)))
    return left * right


def get_gaussian_boundary(data, n_components=5, show=False):
    X = data.reshape(-1, 1)
    lowest_bic = np.infty
    bic = []
    for n_component in range(1, n_components + 1):
        #    gmm = mixture.GaussianMixture(n_components=n_components, covariance_type='spherical').fit(X)
        gmm = GaussianMixture(n_components=n_component, covariance_type='spherical', random_state=1).fit(X)
        bic.append(gmm.bic(X))
        if bic[-1] < lowest_bic:
            lowest_bic = bic[-1]
            best_gmm = gmm
    means = best_gmm.means_.flatten()
    covars = best_gmm.covariances_.flatten()
    weights = best_gmm.weights_.flatten()
    x = []
    if len(means) == 1:
        x.append(0)
        return x

    index = np.argsort(means)
    for i in range(len(index) - 1):
        x.append(split_gaussian(weights[index[i]], weights[index[i + 1]], means[index[i]], means[index[i + 1]],
                                covars[index[i]] ** 0.5, covars[index[i + 1]] ** 0.5))

    if show == True:
        showfigure(weights, means, covars ** 0.5, data, sorted(x))
    return sorted(x)


def draw_hierarchy_cluster(data, show=True):
    Z = cluster.hierarchy.linkage(data, method='complete', optimal_ordering=True)
    if show == True:
        cluster.hierarchy.dendrogram(Z, no_labels=False)
        plt.show()
    index = cluster.hierarchy.cut_tree(Z, n_clusters=[4])
    return index


if __name__ == '__main__':
    data_path = r'Data\TCGA-KIRC\exp.csv'
    data = pd.read_csv(data_path)
    print(data.shape)
    not_zero_index = data.iloc[:, 2:].std(axis=1) != 0
    t = data.loc[not_zero_index, :]

    # label = np.zeros(611, dtype=np.int8)
    # for i, col in enumerate(t.columns[2:]):
    #     if int(col[13:15]) >= 10:
    #         label[i] = 1

    # np.save('Data\TCGA-KIRC\label.npy', label)

    t = t.iloc[:, 1:]
    t.to_csv(r'Data\TCGA-KIRC\exp_processed.csv')
