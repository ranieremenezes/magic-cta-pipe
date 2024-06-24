"""
This script creates the bashscripts necessary to apply "lst1_magic_dl1_stereo_to_dl2.py"
to the DL1 stereo data (real and MC). It also creates new subdirectories associated with
the data level 2. The DL2 files are saved at:
WorkingDirectory/DL2/
and in the subdirectories therein.

Usage:
$ python DL1_to_DL2.py

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


def DL1_to_DL2_MC(target_dir, identification, environment): 
    """
    This function creates the bash scripts to run lst1_magic_dl1_stereo_to_dl2.py on the MC files.
    
    Parameters
    ----------
    target_dir: str
        Path to the working directory
    """
    
    process_name = "DL2_"+target_dir.split("/")[-2:][1]
    RFs_dir = target_dir+"/DL1/MC/RFs"
    
    if not os.path.exists(target_dir+"/DL2"):
        os.mkdir(target_dir+"/DL2")
        
    if not os.path.exists(target_dir+"/DL2/MC"):
        os.mkdir(target_dir+"/DL2/MC")
    
    if not os.path.exists(target_dir+f"/DL2/MC/{identification}"):
        os.mkdir(target_dir+f"/DL2/MC/{identification}")
        
    outputMC = target_dir+f"/DL2/MC/{identification}"
    
    listOfMC = np.sort(glob.glob(target_dir+f"/DL1/MC/{identification}/Merged_Stereo/*.h5"))
    
    np.savetxt(target_dir+f"/DL1/MC/{identification}/Merged_Stereo/list_of_DL1_stereo_files.txt",listOfMC, fmt='%s')

    f = open(f'DL1_to_DL2_MC_{identification}.sh','w')
    f.write('#!/bin/sh\n\n')
    f.write('#SBATCH -p long\n')
    f.write('#SBATCH -J '+process_name+'\n')
    f.write('#SBATCH --mem=40g\n')
    f.write('#SBATCH -N 1\n\n')
    f.write('ulimit -l unlimited\n')
    f.write('ulimit -s unlimited\n')
    f.write('ulimit -a\n\n')
    
    f.write(f"SAMPLE_LIST=($(<{target_dir}/DL1/MC/{identification}/Merged_Stereo/list_of_DL1_stereo_files.txt))\n")
    f.write("SAMPLE=${SAMPLE_LIST[${SLURM_ARRAY_TASK_ID}]}\n")
    f.write(f'export LOG={outputMC}'+'/DL1_to_DL2_${SLURM_ARRAY_TASK_ID}.log\n')
    f.write(f'conda run -n {environment} python lst1_magic_dl1_stereo_to_dl2.py --input-file-dl1 $SAMPLE --input-dir-rfs {RFs_dir} --output-dir {outputMC} --config-file {target_dir}/../config_general.yaml >$LOG 2>&1\n\n')
    f.close()

def main():

    """
    Here we read the config_general.yaml file and call the functions defined above.
    """
    
    
    with open("config_general.yaml", "rb") as f:   # "rb" mode opens the file in binary format for reading
        config = yaml.safe_load(f)
    
    
    target_dir = str(Path(config["directories"]["workspace_dir"]))+"/"+config["directories"]["target_name"]
    environment = config["general"]["environment_name"]

    print("***** Generating bashscripts for DL2...")
    DL1_to_DL2_MC(target_dir, "gammas", environment)
    DL1_to_DL2_MC(target_dir, "protons", environment)
    DL1_to_DL2_MC(target_dir, "protons_test", environment)
    DL1_to_DL2_MC(target_dir, "electrons", environment)
    
    
    print("***** Running lst1_magic_dl1_stereo_to_dl2.py in the DL1 data files...")
    print("Process name: DL2_"+target_dir.split("/")[-2:][1])
    print("To check the jobs submitted to the cluster, type: squeue -n DL2_"+target_dir.split("/")[-2:][1])
    
    #Below we run the bash scripts to perform the DL1 to DL2 cnoversion:
    list_of_DL1_to_DL2_scripts = np.sort(glob.glob("DL1_to_DL2_*.sh"))

    for run in list_of_DL1_to_DL2_scripts:
        os.system(f"sbatch {run}")


if __name__ == "__main__":
    main()

