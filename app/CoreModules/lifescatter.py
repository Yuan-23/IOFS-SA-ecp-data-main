import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import base64
from io import BytesIO

def survivalPlt(lifes, stats):
    # grid3 = pd.read_excel(os.path.join("../", "uploadfiles", "S2_data.xlsx"), index_col=0, header=0)
    # projectNames = np.array(grid3._stat_axis.values.tolist())
    # projectCensors = np.array(grid3.iloc[:, 0]).reshape((1, -1))[0]
    # projectLife = np.array(grid3.iloc[:, 1]).reshape((1, -1))[0]
    deadx = []
    deady = []
    livex = []
    livey = []
    for id,items in enumerate(lifes):
        if stats[id] == 1:
            deadx.append(id)
            deady.append(items)
        else:
            livex.append(id)
            livey.append(items)
    figure = plt.figure(figsize=(15, 3))
    ax = figure.add_subplot(111)
    ax.set_frame_on(b=False)
    # ax.use_sticky_edges(True)
    ax.grid(True, linestyle="-.")
    for key, spine in ax.spines.items():
        # 'left', 'right', 'bottom', 'top'
        if key == 'right' or key == 'top':
            spine.set_visible(False)
    ax.set_xmargin(0)
    ax.set_ymargin(0)
    ax.yaxis.set_label_position("right")
    ax.tick_params(axis="y", direction="inout", pad=-28, labelleft="on", left=False)
    ax.tick_params(axis="x", bottom=False)
    ax.set_xticklabels([])
    ax.scatter(deadx, deady, c="tomato")
    ax.scatter(livex, livey, c="darkturquoise")
    picIO = BytesIO()
    # plt.savefig("down.png", bbox_inches='tight', pad_inches=0.0)
    plt.savefig(picIO, bbox_inches='tight', pad_inches=0.0)
    return base64.encodebytes(picIO.getvalue()).decode()
    # print('data:image/png;base64,' + str(data))
    # plt.show()

if __name__ == '__main__':
    survivalPlt()