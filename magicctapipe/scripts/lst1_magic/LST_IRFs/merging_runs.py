"""
Usage:
$ python merging_runs_and_spliting_training_samples.py

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


def mergeMC(target_dir, identification, environment):
    
    """
    This function creates the bash scripts to run merge_hdf_files.py in all MC runs.
    
    Parameters
    ----------
    target_dir: str
        Path to the working directory
    identification: str
        Tells which batch to create. Options: protons, gammadiffuse
    """
    
    process_name = "merging_"+target_dir.split("/")[-2:][1]
    
    MC_DL1_dir = target_dir+"/DL1/MC"
    if not os.path.exists(MC_DL1_dir+f"/{identification}/Merged_Stereo"):
        os.mkdir(MC_DL1_dir+f"/{identification}/Merged_Stereo")
    
    list_of_nodes = np.sort(glob.glob(MC_DL1_dir+f"/{identification}/Ster*"))
    
    np.savetxt(MC_DL1_dir+f"/{identification}/list_of_nodes.txt",list_of_nodes, fmt='%s')
        
    f = open(f"Merge_{identification}.sh","w")
    f.write('#!/bin/sh\n\n')
    f.write('#SBATCH -p short\n')
    f.write('#SBATCH -J '+process_name+'\n')
    f.write('#SBATCH --mem=7g\n')
    f.write('#SBATCH -N 1\n\n')
    f.write('ulimit -l unlimited\n')
    f.write('ulimit -s unlimited\n')
    f.write('ulimit -a\n\n')
    
    f.write(f"SAMPLE_LIST=($(<{MC_DL1_dir}/{identification}/list_of_nodes.txt))\n")
    f.write("SAMPLE=${SAMPLE_LIST[${SLURM_ARRAY_TASK_ID}]}\n")
    f.write(f'export LOG={MC_DL1_dir}/{identification}/Merged_Stereo'+'/merged_${SLURM_ARRAY_TASK_ID}.log\n')
    f.write(f'conda run -n {environment} python merge_hdf_files.py --input-dir $SAMPLE --output-dir {MC_DL1_dir}/{identification}/Merged_Stereo >$LOG 2>&1\n')        
    
    f.close()
    
    
def main():

    """
    Here we read the config_general.yaml file, split the pronton sample into "test" and "train", and merge the MAGIC files.
    """
    
    
    with open("config_general.yaml", "rb") as f:   # "rb" mode opens the file in binary format for reading
        config = yaml.safe_load(f)
    
    
    target_dir = str(Path(config["directories"]["workspace_dir"]+config["directories"]["target_name"]))
    
    environment = config["general"]["environment_name"]
    
    print("***** Generating mergeMC bashscripts...")
    mergeMC(target_dir, "protons", environment) #generating the bash script to merge the files
    mergeMC(target_dir, "gammadiffuse", environment) #generating the bash script to merge the files
    mergeMC(target_dir, "gammas", environment) #generating the bash script to merge the files 
    mergeMC(target_dir, "protons_test", environment)
    mergeMC(target_dir, "electrons", environment)
    
    print("***** Running merge_hdf_files.py in the MAGIC data files...")
    print("Process name: merging_"+target_dir.split("/")[-2:][1])
    print("To check the jobs submitted to the cluster, type: squeue -n merging_"+target_dir.split("/")[-2:][1])
    
    #Below we run the bash scripts to merge the MAGIC files
    list_of_merging_scripts = glob.glob("Merge_*.sh")

    for run in list_of_merging_scripts:
        os.system(f"sbatch {run}")

if __name__ == "__main__":
    main()


    
    
    
    
    
    
