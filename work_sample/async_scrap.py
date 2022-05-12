from scrap import scrap
from util import utils
import sys
import os
import time

if __name__ == "__main__":

    # Optional filter, useful if get_page(filter_fields=True)
    # git_user_fields = ['followers','following','created_at','updated_at','login','twitter_username']

    # , "commit_from_owners" if adding this to repo_sum_fields will slow down a lot because it consumes API rate
    repo_sum_fields = ["size", "forks", "watchers", "commit_from_owners"]
    input_file = "GR12_handleonly.txt"
    github_handles_file = os.path.join(
        os.path.dirname(__file__), "..", "data", input_file
    )
    handles = scrap.read_handle(github_handles_file)
    scrap.extract_user_github_data(
        repo_sum_fields=repo_sum_fields,
        handle_list=handles,
        result_fn=os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            input_file + "general_user_info.csv",
        ),
        summary_fn=os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            input_file + "summary_user_info.csv",
        ),
        num_processes=9,
    )
# >20 processes may trigger "secondary rate limit"
