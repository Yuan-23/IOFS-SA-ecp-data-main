import numpy as np
import matplotlib
import matplotlib.pyplot as plt

# matplotlib.use('TkAgg')
from app.CoreModules.GMM import get_gaussian_boundary
from app.CoreModules.tools import load_feature_impts_from_dir
import pandas as pd

"""
画出基因重要性的图
"""
if __name__ == '__main__':
#     Data_Path = r'D:\iwsrahc-main\app\data\mRNA\GBM.csv'
#     # Data_Path = r'D:\iwsrahc-main\app\data\microRNA\GBM.csv'
#
#     # df = pd.read_csv(Data_Path)
#
#     # Vimps_Path = r'D:\data\ACC\vimps_Survival_Cox_1_no_permutation'
#     # Vimps_Path = r'D:\data\vimps_Survival_Cox_2_no_permutation'
#     Vimps_Path = r'D:\data\GBM\features2_loops10000_mRNA'
#
#     # vimps = load_feature_impts_from_dir(Vimps_Path, show=True)
#     # # print(vimps[0])
#     #
#     # feature_index = np.argsort(-vimps)  # 反置，则越大越重要，argsort（a,ax）将矩阵a按照ax从小到大排序，返回排序后的下标，所以sorted_index[0]是最大值的下标
#     # for index in feature_index[:5]:
#     #     selected_name = df.columns[index]
#     #     print(index, selected_name, sep=':')
#
#     # #print(vimps)
#     # feature_index = [265, 402, 159, 325, 367, 437]
#     # for index in feature_index:
#     #     print(index, df.columns[index], sep=':')
#
#     # 用来特征选择
#
#     selected_name = []
#     selected_id = []
#     df = pd.read_csv(Data_Path)
#     # 将计算好的特征的P值取出来
    vimps = load_feature_impts_from_dir(r'D:\data\ACC\features3_loops1011_microRNA', show=True)
    print('end')
#
#     # 反置，则越大越重要，argsort（a,ax）将矩阵a按照ax从小到大排序，返回排序后的下标，所以feature_index[0]是最大值的下标
#
#     feature_index = np.argsort(-vimps)
#
#     # 拟合高斯来判断应该取多少特征（最后一个边界）
#     vimps_gau = get_gaussian_boundary(vimps, n_components=20, show=False)
#     print(vimps_gau)
#
#     # 最大边界的值为：vimps_max
#     vimps_max = vimps_gau[len(vimps_gau) - 1]
#     print("最大边界为：", vimps_max)
#
#     # 大于（等于）最大边界的特征则使用
#     for index in feature_index:
#         if feature_index[index] >= vimps_max:
#             selected_name.append(df.columns[index])
#             selected_id.append(index)
#             selectedlists = {"name": selected_name, "id": selected_id}
#             print(index, df.columns[index], sep=':')
#         # print(index, df.columns[index], sep=':')
#
#     # print(selectedlists["name"], selectedlists["id"], sep=':')
# #  print("selectedlists=" + selectedlists)
# # return json.dumps(selectedlists, cls=MyEncoder)

from lifelines.datasets import load_rossi
from lifelines import CoxPHFitter
# rossi = load_rossi()
# cph = CoxPHFitter()
# cph.fit(rossi, 'week', 'arrest')
# cph.print_summary()