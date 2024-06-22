"""
Usage:
$ python spliting_train_test.py

"""

import os
import numpy as np
import glob
import yaml
import logging
from pathlib import Path


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

def split_train_test(target_dir, train_fraction):
    
    """
    This function splits the MC proton sample in 2, i.e. the "test" and the "train" subsamples.
    
    Parameters
    ----------
    target_dir: str
        Path to the working directory
    train_fraction: float
        Fraction of proton MC files to be used in the training RF dataset
    """
    
    proton_dir = target_dir+"/DL1/MC/protons"
    
    if not os.path.exists(proton_dir+"/../protons_test"):
        os.mkdir(proton_dir+"/../protons_test")
        os.mkdir(proton_dir+"/../protons_test/single_node")
        
    
    list_of_runs = np.sort(glob.glob(proton_dir+"/single_node/*.h5"))
    split_percent = int(len(list_of_runs)*train_fraction) # In this case, only 20% of the sample will be moved to the test directory
    for run in list_of_runs[split_percent:]:
        os.system(f"mv {run} {proton_dir}/../protons_test/single_node")

    
def main():

    """
    Here we read the config_general.yaml file, split the pronton sample into "test" and "train", and merge the MAGIC files.
    """
    
    
    with open("config_general.yaml", "rb") as f:   # "rb" mode opens the file in binary format for reading
        config = yaml.safe_load(f)
    
    
    target_dir = str(Path(config["directories"]["workspace_dir"]+config["directories"]["target_name"]))
    
    train_fraction = float(config["general"]["proton_train"])    
    
    #Here we slice the proton MC data into "train" and "test":
    print("***** Spliting protons into 'train' and 'test' datasets...")
    split_train_test(target_dir, train_fraction)
    
    print("Done!")

if __name__ == "__main__":
    main()


    
    
    
    
    
    
