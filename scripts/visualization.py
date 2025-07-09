import seaborn as sns
import matplotlib.pyplot as plt

def plot_heatmap(data, title):
    fig, ax = plt.subplots(figsize = (8, 6))
    sns.heatmap(data, annot = True, cmap = 'Y10rRd', fmt = '.1f', ax = ax)
    ax.set_title(title)
    return fig