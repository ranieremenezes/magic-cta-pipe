import os
import sys
import yaml
import datetime
import pandas as pd


def load_cfg_file(config_file):
    """Load the configuration file (yaml format)

    Parameters
    ----------
    config_file : str
        configuration file, yaml format

    Returns
    -------
    dict
        loaded configurations
    """
    e_ = ("ERROR: can not load the configuration file %s\n"
          "Please check that the file exists and is of YAML format\n"
          "Exiting")
    try:
        cfg = yaml.safe_load(open(config_file, "r"))
    except IOError:
        print(e_ % config_file)
        sys.exit()
    return cfg


def load_cfg_file_check(config_file, label):
    """Load the configuration file (yaml format) and checks that the label
    section is present in the given file, if not it exits

    Parameters
    ----------
    config_file : str
        configuration file, yaml format
    label : str
        label for the desired section

    Returns
    -------
    dict
        loaded configurations
    """
    e_ = ("ERROR: can not load the configuration file %s\n"
          "Please check that the file exists and is of YAML format\n"
          "Exiting")
    l_ = ("ERROR: the configuration file is missing the %s section.\n"
          "Exiting")
    cfg = load_cfg_file(config_file)
    if label not in cfg:
        print(l_ % label)
        sys.exit()
    return cfg


def check_folder(folder):
    """Check if folder exists; if not, it will be created"""
    if not os.path.exists(folder):
        print("Directory %s does not exist, creating it..." % folder)
        os.makedirs(folder)


def load_dl1_data(file, labels=['hillas_params']):
    """Load `dl1/{label}` from dl1 file, h5 format

    Parameters
    ----------
    file : str
        file name
    labels : list, optional
        list of dl1 labels, by default ['hillas_params']

    Returns
    -------
    pandas.core.frame.DataFrame
        data
    """
    data = pd.DataFrame()
    for label in labels:
        data_ = pd.read_hdf(file, key=f'dl1/{label}')
        data_.set_index(['obs_id', 'event_id', 'tel_id'], inplace=True)
        data_.sort_index(inplace=True)
        data = data.append(data_)
    return data


def load_dl1_data_stereo(file):
    """Load `dl1/hillas_params` and `dl1/stereo_params` from dl1 file, 
    h5 format

    Parameters
    ----------
    file : str
        file name

    Returns
    -------
    pandas.core.frame.DataFrame
        data
    """
    data = load_dl1_data(file=file, labels=['hillas_params', 'stereo_params'])
    return data


def out_file_h5(in_file, li, hi):
    """Returns the h5 output file name, from a simtel.gz input file

    Parameters
    ----------
    in_file : str
        Input file
    li : int
        low index
    hi : int
        high index

    Returns
    -------
    str
        h5 output file, absolute path
    """
    f = os.path.basename(in_file)
    out = '_'.join(f.split('_')[:li]+f.split('_')[hi:])
    out = '%s.h5' % out.rstrip('.simtel.gz')
    out = os.path.join(os.path.dirname(in_file), out)
    return out
