import pandas as pd
import time
import json
import networkx as nx


def display_topo(
    filepath: str,
):
    """
    Args:
    , output_1 = "path_graph1.png", output_2 = "path_graph2.png"
        filepath: file to render topology
    """
    df = pd.read_csv(filepath)
    df["vertex2"] = df["vertex2"].apply(lambda x: json.loads(x)["screen_name"])
    df["vertex1"] = df["vertex1"].apply(lambda x: json.loads(x)["screen_name"])
    df = df[df["mentioned"] > 1]
    g = nx.from_pandas_edgelist(
        df, source="vertex1", target="vertex2", edge_attr="mentioned"
    )

    return g
