import json
import pandas as pd


class Feature_Fields:
    """
    A class that manipulate existing features, to generate new features
    """

    def get_length(
        self,
        input_list: list,
        id_field_name: str,
        op_field: str,
        generated_field_name: str = "derived_length",
    ):
        """
        Derive the string length - how much effort user had to create profile etc
        Assumption - UID is unique - in future we need to link user profile from different data sources, i.e.  username in github, and wallet in ETH chain

        Returns: new feature

        Args:
            input_list (list): source data set
            id_field_name (str):
            op_field (str):

        """
        result = []
        for record in input_list:
            new_dict = {}
            new_dict[id_field_name] = record[id_field_name]
            new_dict[generated_field_name] = len(record[op_field])
            result.append(new_dict)

        return result

    def completion_score(
        self,
        input_list: list,
        id_field_name: str,
        var_list: list = [
            "name",
            "company",
            "blog",
            "location",
            "email",
            "bio",
            "hireable",
            "twitter_username",
        ],
    ):
        """
        Derive how incomplete the profile is

        """
        result = []
        for record in input_list:
            cnt = 0
            new_dict = {}
            new_dict[id_field_name] = record[id_field_name]
            for field in var_list:
                if field in record:
                    if (
                        type(record[field]) is str
                        and len(record[field]) > 0
                        and record[field] != "null"
                    ):
                        cnt += 1
                    elif isinstance(field, (int, float)):
                        cnt += 1
            new_dict["filled_count_"] = cnt
            new_dict["profile_fields"] = len(var_list)
            result.append(new_dict)

        return result

    def combine_multi_features(self, field_list):
        """
        An example method to combine say donations, hackathons, repo count to get active index
        """
        pass

    def get_last_n_value(self):
        """
        for the same entity, get last n values_ such as last 2 times user updated the repo
        this may need slow change dimension-like implementation in data warehouse

        """
        pass


class Feature_Process:
    """
    Feature_Process to handle input and output from feature data source
    """

    def read_by_type(self, file_loc, file_type):

        with open(file_loc) as file:
            content = []
            if file_type == "json":
                full_string = file.read()
                full_json = json.loads(full_string)
                content = full_json["contents"]
            elif file_type == "txt":
                lines = file.readlines()
                for line in lines:
                    try:
                        if "{" in line and "}" in line:
                            line_json = json.loads(line)
                            content.append(line_json)
                    except:
                        raise ValueError("Invalid line: " + str(line))
            elif file_type == "csv":
                df = pd.read_csv(file_loc)
                # conver to list of dicts
                content = df.to_dict("records")
            else:
                return NotImplementedError
            return content

    def get_feature_from_file(
        self, file_loc, file_type, sel_features=None, rm_features=None
    ):
        """
        Return features from the data source, optional filter

        Returns:
            list: each element is a dict describing one data row

        Args
            file_loc: file source path
            file_type: 'json' means a template json with 'header' and 'contents' section, 'txt' means each line is a json data row
                json.loads will treat {"key": null} to Python {key:None}
            sel_features: List of feature name whitelist, if not specified, then keep all features
            rm_features: List of feature name blacklist
        """

        content = self.read_by_type(file_loc, file_type)

        self.feature_set_chosen = []
        if sel_features is None:
            return content
        else:

            def filter(dict, sel):
                return {k: v for k, v in dict.items() if k in sel}

            return [filter(a, sel_features) for a in content]

    def append_feature(self, feature_new, in_f_type, input_loc, output_loc, join_key):
        """
        Save new feature to feature storage class instance

        Returns:
            combined records

        Args
            feature_new: list of dict containing new feature
            in_f_type: 'json' means a template json with 'header' and 'contents' section, 'txt' means each line is a json data row
                json.loads will treat {"key": null} to Python {key:None}
            input_loc: source data file location
            output_loc: where to save combined dataset, CSV files default
            join_key: join key to combine features
        """
        content = self.read_by_type(input_loc, in_f_type)
        df_1 = pd.DataFrame(content)
        df_2 = pd.DataFrame(feature_new)

        df_1 = df_1.merge(df_2, on=join_key, how="left")
        joined = df_1.to_dict("records")
        df_1.to_csv(output_loc, header=True, index=False)

        return joined
