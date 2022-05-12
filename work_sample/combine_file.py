import pandas as pd
import os
import test_twitter
from feature.feature import Feature_Process, Feature_Fields
import json
import sys

repo_path = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(repo_path)

# final github_file to generate
gh_file = os.path.join(
    repo_path,
    "data",
    f"combined_gh_tw.csv",
)

# process 2 part of scrap files to combined file
def combine():
    df_result = []
    for n in range(1, 2):
        fn_1 = os.path.join(
            repo_path,
            "data",
            f"GR12_handleonly.txtgeneral_user_info.csv",
        )
        fn_2 = os.path.join(
            repo_path,
            "data",
            f"GR12_handleonly.txtsummary_user_info.csv",
        )
        fn_3 = f"GR12_handleonly.txtsummary_user_info_commits.csv"

        df_1 = pd.read_csv(fn_1, header=0)
        df_2 = pd.read_csv(fn_2, header=0)
        df_result.append(df_1.merge(df_2, how="left", on=["login"]))

    df = pd.concat(df_result, axis=0)
    df.to_csv(
        gh_file,
        index=False,
    )


# add twitter activity summary, change test_twitter.py to specify time range
def export_twitter(
    tw_col=[
        "username",
        "nretweets",
        "nreplies",
        "nlikes",
        "language_count",
        "mentioned",
        "mention_by_ppl",
    ]
):
    test_twitter.run_tests()
    df = pd.read_csv(gh_file)
    tw_file = os.path.join(
        os.path.dirname(__file__), "twitter_search", "scrap_output", "final_summary.csv"
    )
    tw_df = pd.read_csv(tw_file)[tw_col]
    df = df.merge(
        tw_df, how="left", left_on=["twitter_username"], right_on=["username"]
    )
    df.to_csv(
        gh_file,
        index=False,
    )


# example derive feature
def add_feature():
    file = os.path.join(repo_path, "..", "combined_GR12_final.csv")
    my_feature = Feature_Process().get_feature_from_file(file_loc=file, file_type="csv")

    # derive feature: profile completeness
    derived = Feature_Fields().completion_score(my_feature, id_field_name="login")
    sys.exit()
    save_drv = Feature_Process().append_feature(
        feature_new=derived,
        in_f_type="csv",
        input_loc=file,
        output_loc=file,
        join_key=["login"],
    )

    print(save_drv[:5])


if __name__ == "__main__":

    combine()
    export_twitter()
    add_feature()
