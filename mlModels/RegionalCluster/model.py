import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from sklearn.cluster import AgglomerativeClustering
import seaborn as sns


from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

import joblib

from scipy.cluster.hierarchy import dendrogram

import geopandas

def plot_dendrogram(model, **kwargs):
    # Create linkage matrix and then plot the dendrogram

    # create the counts of samples under each node
    counts = np.zeros(model.children_.shape[0])
    n_samples = len(model.labels_)
    for i, merge in enumerate(model.children_):
        current_count = 0
        for child_idx in merge:
            if child_idx < n_samples:
                current_count += 1  # leaf node
            else:
                current_count += counts[child_idx - n_samples]
        counts[i] = current_count

    linkage_matrix = np.column_stack(
        [model.children_, model.distances_, counts]
    ).astype(float)

    # Plot the corresponding dendrogram
    dendrogram(Z=linkage_matrix, labels= data["Región"].tolist(), orientation="right", **kwargs)
import unicodedata
def remove_tildes(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

# Load data 
data = pd.read_csv("Papa.csv")

# EDA

# metric
data["VPH"] = data.produccion*data.precio
data = data.drop(columns=["d-m-y"]).groupby(by="Región", as_index=False).mean()

# remove Nacional row nd changes riogn name
data["Región"] = data["Región"].replace({"papare de Dios":"Madre de Dios"})

data = data[data.Región!="Nacional"].reset_index(level=0, drop=True)
data = data[data.Región!="Lima Metropolitana"].reset_index(level=0, drop=True)

# features to train model
X = data[[col for col in data.columns if col != "Región"]]

# pipeline
pipeline = Pipeline([
    ('scaler', StandardScaler()),
])

# ['sembrada', 'cosechada', 'produccion', 'rendimiento', 'precio', 'VPH']
pipeline.fit(X=X)

# save pipeline
joblib.dump(pipeline, "transform_pipeline.pkl")

# scaling
X = pipeline.transform(X)

# Model

model = AgglomerativeClustering(distance_threshold=0, n_clusters=None)
model = model.fit(X)

# save dendogram
plot_dendrogram(model)
plt.savefig("dendrogram.png", dpi=300)    # save the figure
plt.show()


# selection distance 
model = AgglomerativeClustering(
    n_clusters=None,
    distance_threshold=8,       # number of clusters to form / look up the dendogram
    metric='euclidean',  # distance measure
    linkage='ward'       # ward, complete, average, single
)

labels = model.fit_predict(X)
data["Cluster"] = model.labels_

# geopnadas 
gdf = geopandas.read_file(
    "zip://limites_departamentales.zip!limites_departamentales/DEPARTAMENTOS_inei_geogpsperu_suyopomalia.shp"
)

data["Región"] =  data["Región"].apply(remove_tildes).str.upper().str.strip()
gdf["NOMBDEP"] =  gdf["NOMBDEP"].apply(remove_tildes).str.strip()

# row  dont coinciden
missing = data[~data["Región"].isin(gdf["NOMBDEP"])]
print(missing["Región"].unique())

data.iloc[25,0] = "MADRE DE DIOS"
data = data.rename(columns={"Región": "NOMBDEP"})


# merge dataframe and geopandaframe
gdf = gdf.merge(data, on=["NOMBDEP"])
df = gdf[["NOMBDEP", 'sembrada', 'cosechada', 'produccion', 'rendimiento', 'precio', 'VPH', 'Cluster', 'geometry']].copy()

# plot map
mapping = {
    0: "A",
    1: "B",
    2: "C",
}
from matplotlib.colors import ListedColormap

colors = [
    "#1f77b4",  # color for category 0
    "#ff7f0e",  # color for category 1
    "#2ca02c",  # color for category 2
]

cmap = ListedColormap(colors)

df["ClusterLabel"] = df["Cluster"].map(mapping)



# model gaussian

from sklearn.mixture import GaussianMixture

bic = []
n_components = range(1,20)
for n in n_components:
    gm = GaussianMixture(n_components=n, random_state=0).fit(X)
    bic.append(gm.bic(X))

plt.plot(n_components, bic)
plt.xticks(n_components) 
plt.xlabel("n component")
plt.ylabel("BIC")
plt.grid()
plt.savefig("BIC.png")


## plot cluster and model comparation

fig, axes = plt.subplots(ncols=4, nrows=2, figsize=(20,10))

fig, axes = plt.subplots(ncols=4, nrows=2, figsize=(22, 10))
fig.suptitle("Indicadores Agrícolas de Papa – Perú", fontsize=20, fontweight="bold")

categorias = ['cosechada', 'sembrada', 'produccion', 'rendimiento',
              'precio', 'VPH', 'gm', 'Cluster']

for cat, ax in zip(categorias, axes.ravel()):
    ax.set_axis_off()
    
    # Título del subplot con mayúscula inicial
    ax.set_title(cat.capitalize(), fontsize=12, fontweight="bold")

    if cat in ["gm", "Cluster"]:
        df.plot(
            column=cat,
            categorical=True,
            legend=True,
            ax=ax,
            linewidth=0.5,
            edgecolor="black",
            legend_kwds={
                "loc": "lower left",
                "fontsize": 8
            }
        )
    else:
        df.plot(
            column=cat,
            cmap="YlOrBr",
            legend=True,
            ax=ax,
            linewidth=0.5,
            edgecolor="black",
            legend_kwds={
                "label": cat.capitalize(),
                "orientation": "horizontal",
                "shrink": 0.7,
                "pad": 0.02
            }
        )

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig("region_map_agglomerative.png", dpi=300)    # save the figure
plt.show()