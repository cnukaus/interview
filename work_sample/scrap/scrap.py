import requests
import json
import multiprocessing
import logging
import numpy as np
import time
import math
import pandas as pd
import os
import sys
from collections import Counter

repo_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
)
sys.path.append(repo_path)
from github_scrap.util import utils

TOKEN_FILE = os.path.join(repo_path, "github_scrap", "login.json")

MOZILLA = " ".join(
    [
        "Mozilla/5.0",
        "(Windows NT 10.0; WOW64)",
        "AppleWebKit/537.36",
        "(KHTML, like Gecko)",
        "Chrome/65.0.3325.181",
        "Safari/537.36",
    ]
)

EXTRA_HEADERS = {
    "Referer": "https://github.com/",
    "Host": "github.com",
    "User-Agent": MOZILLA,
}


def _header(token, extra_headers=True):
    return {
        "Authorization": f"token {token}",
        "Authentication": f"token {token}",
        **(EXTRA_HEADERS if extra_headers else {}),
    }


class GitHubCrawl:
    def __init__(self, handle_list):
        """
        set user-agent
        """
        self.login_url = "https://github.com/login"
        self.post_url = "https://github.com/session"

        self.session = requests.Session()
        self.handle_list = handle_list
        self.repo_summary_fields = []

    def set_git_user_fields(self, git_user_fields):
        """
        set customised filter
        """
        self.git_user_fields = git_user_fields

    def set_repo_summary_fields(self, repo_summary_fields):
        """
        set summary filter
        """
        self.repo_summary_fields = repo_summary_fields

    def api_result_has_user(self, response, user):
        if "login" in response:
            return response["login"].lower() == user.lower()
        else:
            print("user: ", user, ". Response: ", response)
        return False

    def filter_profile(self, old_dict, fields):
        """
        Save selected user attribute fields from dict
        """

        return {sel_key: old_dict[sel_key] for sel_key in fields}

    def filter_summary(self, user, token, proxy, allow_fork=False):
        """
        Loop all repository of a user, IF ONLY CALCULATE FORK=False, it will be much faster
        add up numeric fields chosen,
        if fields contains "commit_from_owners" then loop into repo commits to calculate
        user needs exists otherwise will
        Returns:
            summary dict
            repo count
            commit from non-owners dict
        Args:
            user:github_handle
            token:access_token
            proxy: dict of single http and https proxy: {
                                                            "http": "socks5://127.0.0.1:1080",
                                                            "https": "socks5://127.0.0.1:1080",}
            non_fork: only count from original repos in summary TO IMPLEMENT

        """

        def authors_commits(resp, subdict_commits):
            """
            modifies subdict_commits which has all authors commit to a users' repos
            """
            json_data = resp.json()
            for commit_dict in json_data:
                if type(commit_dict) is str:
                    print("DEBUG commit_str", json_data)
                    continue
                if commit_dict.get("author") is None:
                    return
                commit_login = commit_dict["author"].get("login")
                if commit_login in subdict_commits.keys():
                    subdict_commits[commit_login] += 1
                else:
                    subdict_commits[commit_login] = 1

        URL = f"https://api.github.com/users/{user}"
        REPO_URL = URL + "/repos?page=1"
        repo_count = 0
        summary = {}
        subdict_commits = {}
        resp = self.session.get(url=REPO_URL, headers=_header(token, 0), proxies=proxy)

        while True:  # break if there is no next page

            json_resp = resp.json()
            if type(json_resp) == dict:
                # No user was found. {"message": "Not Found"
                summary = json_resp
            else:
                for repo_dict in json_resp:
                    repo_count += 1
                    for field in self.repo_summary_fields:

                        if field == "commit_from_owners":
                            repo_name = repo_dict["name"]
                            print(repo_name)
                            com_url = f"https://api.github.com/repos/{user}/{repo_name}/commits?page=1"
                            commits_content = self.session.get(
                                url=com_url,
                                headers=_header(token, 0),
                                proxies=proxy,
                            )
                            while True and repo_dict.get("fork") is allow_fork:
                                authors_commits(commits_content, subdict_commits)
                                if "next" not in commits_content.links.keys():
                                    break
                                commits_content = self.session.get(
                                    url=commits_content.links["next"]["url"],
                                    headers=_header(token, 0),
                                    proxies=proxy,
                                )  # next page

                            # only retrieve the owner's commit count
                            summary["commits_original_repo"] = subdict_commits.get(user)

                        else:
                            # create record
                            if "total_" + field not in summary.keys():
                                summary["total_" + field] = repo_dict[field]
                                summary["max_" + field] = repo_dict[field]

                            # addition or replacement
                            else:
                                summary["total_" + field] += repo_dict[field]
                                if repo_dict[field] > summary["max_" + field]:
                                    summary["max_" + field] = repo_dict[field]

            if "next" not in resp.links.keys():
                break
            resp = self.session.get(
                url=resp.links["next"]["url"],
                headers=_header(token, 0),
                proxies=proxy,
            )  # next page

        return summary, repo_count, subdict_commits

    def get_github_user_data(
        self,
        semaphore,
        i,
        handle_list,
        token,
        f_type,
        verbose,
        filter_fields,
        return_dict,
        proxy,
    ):
        """
        Gets the handle_list info running in a single process.
        Return
            using multiprocessing mangaged return_dict to implicitly return value

        Args
                semaphore to tell if API rate limit is reached, 5k/hour
                Unique id for current process
                List of handles that we need to get info on.
                 token authentication token
                f_type file format, default to by line
                verbose
                filter_fields flag for filtering
                The multiprocessing dictionary to store the results in.
                proxy dict


        """
        cnt_not_found = 0
        user_result_lines = []
        repo_summary_lines = []
        commit_lines = []

        not_initial_comma = False
        not_initial_comma_2 = False
        for user in handle_list:
            if not semaphore.value:
                print("API rate limit reached, process sleep 1 hr")
                time.sleep(3601)
                semaphore.value = 1  # clear flag after waiting

            if verbose is True:
                logging.basicConfig(
                    format="%(message)s",
                    level=logging.INFO,
                )
                logging.info(f"user {user}")
            else:
                logging.basicConfig(format="%(levelname)s: %(message)s")

            URL = f"https://api.github.com/users/{user}"
            r = self.session.get(url=URL, headers=_header(token, 0), proxies=proxy)
            user_result = json.loads(r.text)

            # skip excution and enter 3600 seconds wait
            if (
                "API rate limit exceeded" in r.text
                or "a secondary rate limit" in r.text
            ):
                semaphore.value = 0
                continue
            if filter_fields:
                user_result = self.filter_profile(user_result, self.git_user_fields)

            user_exists = self.api_result_has_user(user_result, user)
            if not user_exists:
                cnt_not_found += 1
                user_result = {}  # remove error msg of blank user
                user_result["login"] = user
                user_result["handle_status"] = "NOT EXISTS"

            real_username = user_result["login"]
            if f_type == "json":
                if not_initial_comma:
                    user_result_lines.append(",")
                user_result_lines.append(json.dumps(user_result))
                not_initial_comma = True
            else:
                user_result_lines.append(json.dumps(user_result))

            # create summary fields from https://api.github.com/users/{user}/repos
            if user_exists and len(self.repo_summary_fields) > 0:

                repo_summary_result, repo_count, commit_other = self.filter_summary(
                    user, token, proxy
                )
                repo_summary_result["login"] = real_username
                repo_summary_result["repo_count"] = repo_count
                if f_type == "json":
                    if not_initial_comma_2:
                        repo_summary_lines.append(",")
                    repo_summary_lines.append(json.dumps(repo_summary_result))
                    commit_lines.append(json.dumps(commit_other))
                    not_initial_comma_2 = True
                else:
                    repo_summary_lines.append(json.dumps(repo_summary_result))
                    commit_lines.append(json.dumps(commit_other))

        return_dict[str(i)] = [
            user_result_lines,
            repo_summary_lines,
            commit_lines,
            cnt_not_found,
        ]

    def get_pages_in_parallel(
        self,
        token,
        result_fn,
        summary_fn,
        f_type="csv",
        verbose=True,
        filter_fields=False,
        num_processes=1,
        proxy={},
    ):
        """
        Gets the github page info in parallel.

        Return
            number of users not found in api.github.com

        Args

                token authentication token
                result_fn filename for output
                f_type file format, default 'csv' will convert to csv, 'json' will combine all records in a single json array, otherwise save each json object to a line
                summary_fn optional summary output file name
                verbose
                filter_fields flag for filtering
                proxy dict of single http and https proxy: {
                                                            "http": "socks5://127.0.0.1:1080",
                                                            "https": "socks5://127.0.0.1:1080",}

        output: writing to 2 files:

            result_fn - full user information
            summary_fn - each line summarise metrics such as stared of forked (specified by user) from total repositories
        """

        cnt_not_found = 0

        chunked = self.split_rate_limit()
        combined_result = []
        combined_summary = []
        combined_commits = []

        for file_cnt, allowed_lists in enumerate(chunked):

            manager = multiprocessing.Manager()
            return_dict = manager.dict()
            jobs = []
            semaphore = multiprocessing.Value("i", 1)

            # Split the handles into lists of approximately equal size.
            handle_lists = np.array_split(allowed_lists, num_processes)
            handle_lists = [list(handle) for handle in handle_lists]

            for i in range(num_processes):
                p = multiprocessing.Process(
                    target=self.get_github_user_data,
                    args=(
                        semaphore,
                        i,
                        handle_lists[i],
                        token,
                        f_type,
                        verbose,
                        filter_fields,
                        return_dict,
                        proxy,
                    ),
                )
                jobs.append(p)

            for proc in jobs:
                proc.start()

            # Wait for processes to complete and collect results
            for proc in jobs:
                proc.join()

            # Add new game runs to list of game runs
            result_lines = []
            summary_lines = []
            commit_lines = []
            for worker_values in return_dict.values():
                (
                    w_result_lines,
                    w_summary_lines,
                    w_commit_lines,
                    w_cnt_not_found,
                ) = worker_values
                result_lines.extend(w_result_lines)
                summary_lines.extend(w_summary_lines)
                commit_lines.extend(w_commit_lines)
                cnt_not_found += w_cnt_not_found

            combined_result.extend(result_lines)
            combined_summary.extend(summary_lines)
            combined_commits.extend(commit_lines)
            if file_cnt < len(chunked) - 1:
                print("Now sleep 1 hr to avoid exceeding API rate limit")
                time.sleep(3601)

        # Add batch index to filename.
        split_txt = result_fn.rsplit(".", 1)
        assert len(split_txt) == 2
        file_name, file_ext = split_txt
        split_txt = summary_fn.rsplit(".", 1)
        assert len(split_txt) == 2
        summary_fn, file_ext = split_txt

        # Write current batch to file
        if f_type == "csv":
            combined_dict = [json.loads(d) for d in combined_result]
            df = pd.json_normalize(combined_dict)
            # data formatting
            if "id" in df.columns:
                df.fillna({"id": 0}, inplace=True)
                df["id"] = df["id"].astype("int32")
            df.to_csv(f"{file_name}.{file_ext}", header=True, index=False)

            summary_dict = [json.loads(d) for d in combined_summary]
            df = pd.json_normalize(summary_dict)
            df.to_csv(f"{summary_fn}.{file_ext}", header=True, index=False)

            commit_dict = [json.loads(d) for d in combined_commits]
            df = pd.json_normalize(commit_dict)
            df.to_csv(f"{summary_fn}_commits.{file_ext}", header=True, index=False)
        else:
            with open(
                f"{file_name}.{file_ext}", "w", encoding="utf-8"
            ) as result_file, open(
                f"{summary_fn}.{file_ext}", "w", encoding="utf-8"
            ) as summary_file, open(
                f"{summary_fn}_commits.{file_ext}", "w", encoding="utf-8"
            ) as commits_file:

                if f_type == "json":
                    combined_result[0] = "[" + combined_result[0]
                    combined_result[-1] = combined_result[-1] + "]\n"
                    combined_summary[0] = "[" + combined_summary[0]
                    combined_summary[-1] = combined_summary[-1] + "]\n"
                    combined_commits[0] = "[" + combined_commits[0]
                    combined_commits[-1] = (
                        combined_commits[-1] + "]\n"
                    )  # Write to results file
                for line in combined_result:
                    result_file.write(line + "\n")

                # Write to summary files
                for line in combined_summary:
                    summary_file.write(line + "\n")
                for line in combined_commits:
                    commits_file.write(line + "\n")
        return cnt_not_found

    def split_rate_limit(self, api_rate=5000):
        """
        api_rate hourly 5000, if summary_fiels populated then doubled requests
        """

        if len(self.repo_summary_fields) > 0:
            api_rate = api_rate / 2
        num_lines = len(self.handle_list)
        print("total lines:", num_lines)
        num_batches = math.ceil(num_lines / api_rate)
        print("total batches:", num_batches)
        chunked = []

        if num_batches > 1:

            for i in range(num_batches):
                chunk_start = int(i * api_rate)
                chunk_end = int((i + 1) * api_rate)
                if i <= num_batches - 1:
                    print(chunk_start, chunk_end)
                    chunked.append(self.handle_list[chunk_start:chunk_end])
                else:
                    chunked.append(self.handle_list[chunk_start:])
        else:
            chunked.append(self.handle_list)

        return chunked

    def login(self, token):
        """
        original method, not triggering error, but has 60/hour call rate limit
            {        "utf8": "✓",
            "authenticity_token": self.parse_loginPage(),
            "login": user_name,
            "password": password}
        returns (success?, code, response)
        """

        login_html = self.session.get(url=self.login_url, headers=_header(token))
        code = login_html.status_code
        print(code, "is return code")
        return (code == 200, code, login_html)


def read_handle(
    github_handles_file,
    handle_filename_has_header=True,
):
    # Extract the handles
    with open(github_handles_file, "r") as c:
        contents = c.readlines()
        print(f"Parsing file: {github_handles_file}")
    handle_list = [
        i.strip() for i in contents[handle_filename_has_header:] if i not in ["", "\n"]
    ]
    return handle_list


def extract_user_github_data(
    repo_sum_fields,
    handle_list,
    config_file=TOKEN_FILE,
    result_fn=os.path.join(repo_path, "data", "general_user_info.csv"),
    summary_fn=os.path.join(repo_path, "data", "repo_summary_info.csv"),
    num_processes=6,
):
    """

    Args:
        repo_sum_fields: which fields to summarise
        handle_list
        config_file: contains github token
        result_fn: main output file name
        summary_fn: summary output file name
        num_processes: parallel scrap number
    """
    # Init the GitHubCrawler
    run = GitHubCrawl(handle_list)

    # Set the summary fields
    run.set_repo_summary_fields(repo_sum_fields)

    # Setup the token credentials
    print("reading config from: ", config_file)
    token = utils.load_config(config_file)["github"]["token"]
    success, code, resp = run.login(token)
    print(
        requests.Session()
        .get(
            url="https://api.github.com/rate_limit",
            headers=_header(token, 0),
        )
        .json()
    )
    start = time.time()
    if success:
        print(
            "To select only certain fields: call get_pages_in_parallel(filter_fields=True)"
        )

        users_not_found = run.get_pages_in_parallel(
            token,
            result_fn=result_fn,
            summary_fn=summary_fn,
            f_type="csv",
            num_processes=num_processes,
        )
        if users_not_found > 0:
            print(f"{users_not_found} handles not found in api.github.com")
    else:
        print("Error, no continue")
        print(code)
        print(resp)
    end = time.time()
    lapsed_min = (end - start) / 60
    print(f"{lapsed_min}  minutes used")
    print(
        requests.Session()
        .get(
            url="https://api.github.com/rate_limit",
            headers=_header(token, 0),
        )
        .json()
    )
