from lifelines import CoxPHFitter
import pandas as pd
import os


if not os.listdir(r'D:\data\ACC\features3_loops1000_microRNA'):
    print('fine')
else:
    print('flskdjfl')

# df = pd.DataFrame({
#     'T': [5, 3, 9, 8, 7, 4, 4, 3, 2, 5, 6, 7],
#     'E': [1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0],
#     'var': [0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2],
#     'age': [4, 3, 9, 8, 7, 4, 4, 3, 2, 5, 6, 7],
#  })
#
#
# cph = CoxPHFitter()
# cph.fit(df, 'T', 'E')
# cph.print_summary()
# cph.predict_median(df)
# p1 = cph._compute_p_values()
# print('p1:', p1)
