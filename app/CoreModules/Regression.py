from lifelines.datasets import load_rossi
from lifelines import CoxPHFitter, exceptions, KaplanMeierFitter
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import random, os, time
from app.CoreModules.tools import Vimps, draw_hierarchy_cluster, load_feature_impts_from_dir
from tqdm import tqdm
import concurrent.futures as cf
import warnings
from numpy.linalg import LinAlgError

warnings.filterwarnings('ignore')


def train_and_trainscore_permutation(X, duration_col, event_col):
    # 进行premutation
    vimps = np.zeros((X.shape[1]))

    # Performance1，打乱前
    cph1 = CoxPHFitter(penalizer=0.1)

    # cph1.fit(X, duration_col=duration_col, event_col=event_col)  # , show_progress=True, step_size=0.1)
    try:
        #将模型拟合到数据集
        cph1.fit(X, duration_col=duration_col, event_col=event_col)  # , show_progress=True, step_size=0.1)
    # except LinAlgError:
    #     print('/n*' * 10)
    #     return False, vimps
    except exceptions.ConvergenceError as e:
        # print(e)
        # raise e
        #不收敛则将vimps置零
        return False, vimps

    #计算P值
    p1 = cph1._compute_p_values()

    # print("p1=",p1)

    # 如果 所有的p值都大于0.1 则跳过下面的permutation, 直接返回vimps
    if any(p1 <= 0.1):
        pass
        # print(p1)
    else:
        return False, vimps

    # 否则 permutation  （+2是生存时间和生存状态）
    for i in np.where(p1 <= 0.1)[0]+2:
        # for i in range(2, X.shape[1]):
        # permutation，打乱
        t = np.random.permutation(X.iloc[:, i])
        X_copy = X.copy()
        X_copy.iloc[:, i] = t

        # Performance2，打乱后
        cph2 = CoxPHFitter(penalizer=0.1)
        # 将模型拟合到数据集
        try:
            cph2.fit(X_copy, duration_col=duration_col, event_col=event_col)
        except:
            raise('This is my error code recommand.')
        #获得P值
        p2 = cph2._compute_p_values()
        # print(p2)
        # permutation = Performance1（打乱前） - Performance2（打乱后）
        vimps[i] = np.log2(p2[i - 2]) - np.log2(p1[i - 2])

    return True, vimps


def train_and_trainscore(X, duration_col, event_col):
    # 不进行premutation
    vimps = np.zeros((X.shape[1]))
    # Performance1
    cph1 = CoxPHFitter()  # penalizer=0.1)
    try:
        cph1.fit(X, duration_col=duration_col, event_col=event_col)  # , show_progress=True, step_size=0.1)
    except exceptions.ConvergenceError:
        return False, vimps

    p1 = cph1._compute_p_values()
    # 如果 所有的p值都大于0.1 则跳过下面的permutation, 直接返回vimps
    if any(p1 <= 0.1):
        pass
        # print(p1)
    else:
        return False, vimps

    for i in np.where(p1 <= 0.1)[0] + 2:
        # permutation = Performance1 - Performance2
        vimps[i] = - np.log2(p1[i - 2])

    return True, vimps


def extract_feature_for_acc(X, y, n_features, times, save_dir):
    print('I am in extract_feature_for_acc')
    # get n features from X randomly except 'Survival stata/day'


    feature_index = range(2, X.shape[1])  # 2: 'Survival stata' and 'Survival day'
    vimps_ans = Vimps(X.shape[1], save_dir)

    for _ in tqdm(range(times)):
        data_train, data_test, _, _ = train_test_split(X, X.loc[:, y['Survival state']],
                                                       stratify=X.loc[:, y['Survival state']],
                                                       test_size=0.3, random_state=0)
        extract_features = [0, 1] + random.sample(feature_index, n_features)
        # Flag, vimps = train_and_trainscore_permutation(X.iloc[:, extract_features], y['Survival day'], y['Survival state'])
        Flag, vimps = train_and_trainscore_permutation(data_train.iloc[:, extract_features], y['Survival day'],
                                                       y['Survival state'])
        # This is an error code line
        # Flag, vimps = train_and_trainscore_permutation(X.iloc[:, extract_features], y['Survival state'], y['Survival day'])
        # Flag, vimps = train_and_trainscore(X.iloc[:, extract_features], y['Survival state'],y['Survival day'])

        # feature score. SHUFFLE.
        # if Flag == True:
        feature_dict = {i: vimp for i, vimp in zip(extract_features, vimps)}
        vimps_ans.update(feature_dict)
    # return vimps_ans
    vimps_ans.save_vimps()


def permutation(rossi, duration_col='week', event_col='arrest', permu_col=0):
    cph1 = CoxPHFitter()
    cph1.fit(rossi, duration_col=duration_col, event_col=event_col)
    p1 = cph1._compute_p_values()

    print(p1)
    # cph1.print_summary()
    t = np.random.permutation(rossi.iloc[:, permu_col])
    rossi.iloc[:, permu_col] = t

    cph2 = CoxPHFitter()
    cph2.fit(rossi, duration_col=duration_col, event_col=event_col)
    p2 = cph2._compute_p_values()
    print(p2)
    impts = np.log2(p2[permu_col]) - np.log2(p1[permu_col])
    return impts


if __name__ == '__main__':
    selectedlists={}
    #每次抽 n_features 个特征
    n_features = 5

    WORK_PATH = r'.'
    # Data_Path = r'D:\iwsrahc-main\app\uploadfiles\HhBhkNKT.xlsx'
    # Data_Path = r'D:\iwsrahc-main\app\data\mRNA\ACC.csv'
    Data_Path = r'D:\iwsrahc-main\app\data\microRNA\ACC.csv'
    # Data_Path = r'D:\BBD_DATA\TCGA_DATA\TCGA-GBM\mi_RNAdata_survial_processed.csv'
    file_name = os.path.split(Data_Path)[-1].split('.')[0]
    vimps_save_dir = os.path.join(WORK_PATH, f'D:/Data/{file_name}/vimps_Survival_Cox_{n_features}_permutation')

    #vimps_save_dir = os.path.join(WORK_PATH, f'D:\Data/vimps_Survival_Cox_{n_features}_no_permutation')
    if not os.path.exists(vimps_save_dir):
        os.makedirs(vimps_save_dir)

    # data = pd.read_excel(Data_Path)
    # data = pd.read_excel(Data_Path)
    data = pd.read_csv(Data_Path)
    # with open('gene_index2name.txt', 'w') as f:
    #     for i, ensg in enumerate(data.columns):
    #         print(i, ensg, sep='\t', file=f)

    # not_zero_index = data.std(axis=0) != 0
    # data = data.loc[:, not_zero_index]
    del data['Unnamed: 0']
    # plt.plot(data.std(axis=0),'.k')
    # plt.show()
    #########################
    # vimps = np.load(r'Data\vimps_Survival_Cox\vimps_and_count_1638169501.5265687.npy')
    # t = data.loc[:,['Survival state', 'Survival day', 'hsa-miR-10b']]
    # p = permutation(t, 'Survival state', 'Survival day' , 2)
    #########################
    # data.iloc[:, 2:] =  ( data.iloc[:, 2:] - data.iloc[:, 2:].mean(axis=0) )/ data.iloc[:, 2:].std(axis=0)
    # data_train, data_test, _, _ = train_test_split(data, data.loc[:, 'Survival state'],stratify=data.loc[:, 'Survival state'], test_size=0.3, random_state=0)
    y = {'Survival state': 'vital_status', 'Survival day': 'days_to_death'}

    data_train, data_test, _, _ = train_test_split(data, data.loc[:, y['Survival state']],
                                                   stratify=data.loc[:, y['Survival state']], test_size=0.3,
                                                   random_state=0)
    # num_of_feature = data.shape[1] - 2
    # index = range(num_of_feature)

    works = 10  # number of file
    times = 1000  # time for file
    # y = {'Survival state': 'Survival state', 'Survival day': 'Survival day'}
    # 10b:184   222:431

    # vimps = extract_feature_for_acc(data_train, y, n_features, times, vimps_save_dir)
    # print('*' * 20)
    print('Start: ', time.ctime())
    jobs = []
    with cf.ProcessPoolExecutor(max_workers=14) as pool:
        for i in range(14):
            jobs.append(pool.submit(extract_feature_for_acc, data_train, y, n_features, times, vimps_save_dir))
    print('End: ', time.ctime())



# #### 选出重要特征之后运行
# # 10b:19, 222:127, 265
# index = draw_hierarchy_cluster(data.iloc[:,265].values.reshape(-1,1),n_clusters=[2],  show=True)
# index = index.reshape(-1,)
# # data.loc[index==1, 'Survival state']
#
# kmf = KaplanMeierFitter()
#
# T, E = data.iloc[:,1].values, data.iloc[:,0].values
# ix = (index != 1)
# kmf.fit(T[~ix], E[~ix], label='cluster0')
# ax = kmf.plot_survival_function()
#
# kmf.fit(T[ix], E[ix], label='cluster1')
# ax = kmf.plot_survival_function(ax=ax)
# plt.title(data.columns[265])
# plt.show()

