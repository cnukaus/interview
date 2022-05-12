import unittest
from feature.feature import Feature_Process, Feature_Fields
import json
import os
import twitter_search.get_data as get_data
import io


class TestTwitter(unittest.TestCase):
    def test_extract(self):

        filedir = os.path.dirname(os.path.abspath(__file__))
        file = os.path.join(filedir, "..", "data", "combined_gh_tw.csv")
        fav_features = ["twitter_username"]
        # Test 1, get twitter feature from crawled github dataset
        my_feature = Feature_Process().get_feature_from_file(
            file_loc=file, file_type="csv", sel_features=fav_features
        )
        twitter_users = [
            d.get("twitter_username")
            for d in my_feature
            if d.get("twitter_username") is not None
            and d.get("twitter_username") == d.get("twitter_username")
        ]
        print("Test selected features: ", len(my_feature))

        # feed git twitter crawler
        df_tweets = get_data.extract_tweet(twitter_users, days_to_search=10)
        captured_file = os.path.join(
            get_data.current_script_folder,
            get_data.output_folder,
            "tweet_of_interest.csv",
        )

        df_tweets.to_csv(captured_file, header=True, index=False)


class TestTopology(unittest.TestCase):
    def test_create_topo(self):
        captured_file = os.path.join(
            get_data.current_script_folder,
            get_data.output_folder,
            "tweet_of_interest.csv",
        )
        get_data.generate_summary(captured_file, "network_topo.csv")

    def test_topo(self):

        get_data.extract_topo("network_topo.csv", show=False)


def run_tests():

    test_classes_to_run = [TestTwitter, TestTopology]

    loader = unittest.TestLoader()

    suites_list = []
    for test_class in test_classes_to_run:
        suite = loader.loadTestsFromTestCase(test_class)
        suites_list.append(suite)

    big_suite = unittest.TestSuite(suites_list)

    runner = unittest.TextTestRunner()
    results = runner.run(big_suite)


if __name__ == "__main__":
    # unittest.main(warnings="ignore")
    run_tests()
