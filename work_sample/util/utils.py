import configparser
import logging as log
import glob, os
import json



def load_config(config_addr):
    "load JSON"
    try:
        with open(config_addr, "r") as f:
            _spec = json.load(f)
            return _spec
    except Exception as err:
        raise Exception(err)

