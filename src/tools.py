
import yaml


def build_from_config(file_name):
    """
    Build a petrinet from a yaml config file
    """
    with open(file_name) as f:
        dict_config = yaml.load(f)

    places, transitions = {}, {}
