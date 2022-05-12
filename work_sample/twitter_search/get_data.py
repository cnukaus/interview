import pandas as pd
import numpy as np
from itertools import groupby
import ast
import json
from collections import Counter
import twint
import operator
from . import list_graph
from . import topology
import os
from datetime import datetime, timedelta
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path

current_script_folder = os.path.dirname(__file__)
output_folder = os.path.join(current_script_folder, "scrap_output")
Path(output_folder).mkdir(exist_ok=True)


def get_tweets(
    keyword_list: list,
    user_list: list,
    from_dt: str,
    to_dt: str,
    store_as_csv: bool,
    store_as_pandas: bool,
    hide_progress=True,
    tweet_limit: int = 80,
):
    """
    given a list of twitter users, plus optional keyword list, search and get tweets result

    Return
        dataframe of tweets meeting serach condition

    Args:
        keyword_list: optional keywords to search on top of user_list
        user_list: list of users to search
        from_dt: date search range begin
            YYYY-MM-DD
        to_dt: date search range end
            YYYY-MM-DD
        store_as_csv: boolean. indicate output type as CSV
        store_as_pandas: boolean. indicate output type as pandas
        hide_progress: boolean. indicate to turn off detailed message
        tweet_limit: max number of tweets from each Twitter user

    """
    c = twint.Config
    c.Store_csv = store_as_csv
    c.Pandas = store_as_pandas
    c.Hide_output = hide_progress
    c.Since = from_dt
    c.until = to_dt

    # Number of tweets to pull
    c.Limit = tweet_limit

    df = pd.DataFrame()

    for user in user_list:
        c.Username = user
        for keyword in keyword_list:
            c.Search = keyword
            twint.run.Search(c)
            df_result = twint.storage.panda.Tweets_df
            df = df.append(df_result)
        if not keyword_list:
            twint.run.Search(c)
            df_result = twint.storage.panda.Tweets_df
            df = df.append(df_result)

    return df


def most_replied(df: pd.DataFrame(), col_name: str = "reply_to"):
    """
    which user is most refered to in reply

    Args:
        df: dataframe of tweets extracted
        col_name: name of reply to user

    Returns:
        dataframe
    """
    df = df.loc[df[col_name].notna()]
    list_replies = [
        row[col_name][1:-1] for index, row in df.iterrows()
    ]  # [1:-1] removes the surrounding square bracket, just need dicts of each replied
    new_list = []
    i, j, k = 0, 0, 0
    for str_or_tuple in list_replies:
        str_or_tuple = ast.literal_eval(str_or_tuple)
        if isinstance(str_or_tuple, tuple):
            new_list += [x for x in list(str_or_tuple)]
            i += 1
        elif isinstance(str_or_tuple, dict):
            new_list.append(str_or_tuple)
            j += 1
        else:
            k += 1
    if k > 1:
        print(
            "count of multiple mention in tweet {}, single {}, exception{}".format(
                i, j, k
            )
        )
    return new_list


def run_most_replied(df: pd.DataFrame()):
    contents = most_replied(df)
    contents_str = [json.dumps(x) for x in contents]
    counted = Counter(contents_str)
    rev = {k: v for k, v in counted.items()}


def build_graph(
    df, twitter_graph, col_name_list=["reply_to", "user_id", "username", "name"]
):
    """
    build the graph by recording vertex 1 to vertex 2

    [row[col_name_list]][0][0] is the content, not series column name, [0][1] shows first value of user_id
    convert dict type vertext to string, because dict can't be hashable key. for list_graph storage - v in self.graph fails

    Args:
        df: tweets captured
        twitter_graph: object of graph representation
    """

    df = df.loc[df[col_name_list[0]].notna()]

    for index, row in df.iterrows():
        vertex = {}
        vertex["id"] = [row[col_name_list]][0][1]
        vertex["screen_name"] = [row[col_name_list]][0][2]
        vertex["name"] = [row[col_name_list]][0][3]
        str_vertex = json.dumps(vertex)

        twitter_graph.add_vertex(str_vertex)
        reply = [row[col_name_list]][0][0]
        reply = ast.literal_eval(reply)
        for vertex_2 in [x for x in list(reply)]:
            str_vertex_2 = json.dumps(vertex_2)
            twitter_graph.add_vertex(str_vertex_2)
            twitter_graph.add_edge(str_vertex, str_vertex_2, 1, verbose=True)

    return twitter_graph


def highest_talked(twitter_graph):
    """
    works for list_graph
    """
    list_vertex2 = []
    for vertex in twitter_graph.graph:

        for edges in twitter_graph.graph[vertex]:
            list_vertex2.append([vertex, edges[0], edges[1]])

    df = pd.DataFrame(list_vertex2, columns=["vertex1", "vertex2", "mentioned"])
    df["user_id"] = df["vertex2"].apply(lambda x: int(json.loads(x)["id"]))
    df["username"] = df["vertex2"].apply(lambda x: json.loads(x)["screen_name"])
    df["name"] = df["vertex2"].apply(lambda x: json.loads(x)["name"])
    return df


def sum_to_account(
    df,
    key_col=["user_id", "username", "name"],
    value_col=[
        "replies_count",
        "retweets_count",
        "likes_count",
        "hashtags",
        "cashtags",
    ],
    value_2_col="lan",
    key_2_name="language_count",
):
    """
    summarise chosen metrics to user level

    Returns:
        summarised user metrics

    Args:
        df: dataframe of tweets extracted
        key_col: fields retained in aggregation
        value_col: numeric values to sum up
        key_2_name: derived field name for value_2_col count unique
        value_2_col: which field to do count unique

    """
    df_summary = df.groupby(key_col)[value_col].sum()
    df_summary[key_2_name] = df.groupby(key_col)[value_2_col].nunique()
    return df_summary


def count_word_freq(df, column_name="tweet"):

    # to combine each ppl's words, then get group by freq
    stop = stopwords.words("english")
    newStopWords = ["hello", "hi", "hey", "im", "get"]
    stop.extend(newStopWords)
    df[column_name] = df[column_name].str.replace("[^\w\s]", "").str.lower()
    df[column_name] = df[column_name].apply(
        lambda x: " ".join([item for item in x.split() if item not in stop])
    )
    df[column_name].str.split(expand=True).stack().value_counts()


def extract_tweet(
    user_list,
    keywords=[],
    to_date=datetime.today().strftime("%Y-%m-%d"),
    days_to_search=5,
):
    """
    Specify a given start date and number of days to search

    Args:
        user_list: list of username
        keywords: list of additional tweet keywords
        to_date: end of search date range, default to today
        days_to_search: number of days to search until to_date

    Return:
        dataframe of tweet details
    """

    from_date = datetime.today() - timedelta(days_to_search)
    from_date = from_date.strftime("%Y-%m-%d")
    df_tweets = get_tweets(
        from_dt=from_date,
        to_dt=to_date,
        keyword_list=keywords,
        user_list=user_list,
        store_as_csv=False,
        store_as_pandas=True,
        tweet_limit=200,
    )

    print("total tweets searched: ", len(df_tweets))
    return df_tweets


def generate_summary(tweet_file, output_file, summary_file="final_summary.csv"):
    """
    using tweet details to:
        1. create summary of retweet, reply and like count
        2. create relationship by number of times between 2 users, save to file for topology
        3. append summariesd relation to user, save to summary file

    Arg:
        tweet_file: extraction format from twint
        output_file: topology file between any 2 users that have conversations
        summary_file: behaviour summary by user

    """

    df = pd.read_csv(tweet_file)
    df[df.isin(["[]"])] = np.nan

    fields_to_sum = ["nretweets", "nreplies", "nlikes"]
    df_summary = sum_to_account(df, value_col=fields_to_sum, value_2_col="language")
    df_summary.reset_index(level=["username", "name"], inplace=True)

    graph_result = list_graph.SimpleGraph()
    build_graph(df, graph_result)
    df_graph = highest_talked(graph_result)

    topo_file_path = os.path.join(current_script_folder, output_folder, output_file)
    df_graph.to_csv(topo_file_path, index=False)

    df_graph_agg = (
        df_graph.groupby(["user_id", "username", "name"])["mentioned"].sum().to_frame()
    )
    df_graph_agg["mention_by_ppl"] = df_graph.groupby(["user_id", "username", "name"])[
        "vertex1"
    ].nunique()

    summary_file_path = os.path.join(current_script_folder, output_folder, summary_file)
    df_summary = pd.merge(df_summary, df_graph_agg, how="left", on=["user_id"])
    df_summary.to_csv(summary_file_path)


def extract_topo(output_file, show=True):

    output_1 = os.path.join(current_script_folder, output_folder, "path_graph1.png")
    output_2 = os.path.join(current_script_folder, output_folder, "path_graph_net.png")
    topo_file_path = os.path.join(current_script_folder, output_folder, output_file)

    draw_graph = topology.display_topo(topo_file_path)

    nx.draw_networkx(draw_graph, with_labels=True)
    plt.savefig(output_1)
    if show:
        plt.show()

    nx.draw_circular(draw_graph, with_labels=True)
    plt.savefig(output_2)
    if show:
        plt.show()
