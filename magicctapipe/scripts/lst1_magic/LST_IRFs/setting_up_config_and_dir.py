"""
Standard usage:
$ python setting_up_config_and_dir.py

"""

import os
import glob
import yaml
from pathlib import Path

def config_file_gen(ids, target_dir):
    
    """
    Here we create the configuration file needed for transforming DL0 data in DL1
    """
    
    f = open(target_dir+'/config_step1.yaml','w')
    f.write("directories:\n    target: "+target_dir+"\n\n")    
    f.write("mc_tel_ids:\n    LST-1: "+str(ids[0])+"\n    LST-2: "+str(ids[1])+"\n    LST-3: "+str(ids[2])+"\n    LST-4: "+str(ids[3])+"\n    MAGIC-I: "+str(ids[4])+"\n    MAGIC-II: "+str(ids[5])+"\n\n")
    
    f.write('LST:\n    image_extractor:\n        type: "LocalPeakWindowSum"\n        window_shift: 4\n        window_width: 8\n\n')
    f.write('    increase_nsb:\n        use: true\n        extra_noise_in_dim_pixels: 1.27\n        extra_bias_in_dim_pixels: 0.665\n        transition_charge: 8\n        extra_noise_in_bright_pixels: 2.08\n\n')
    f.write('    increase_psf:\n        use: false\n        fraction: null\n\n')
    f.write('    tailcuts_clean:\n        picture_thresh: 8\n        boundary_thresh: 4\n        keep_isolated_pixels: false\n        min_number_picture_neighbors: 2\n\n')
    f.write('    time_delta_cleaning:\n        use: true\n        min_number_neighbors: 1\n        time_limit: 2\n\n')
    f.write('    dynamic_cleaning:\n        use: true\n        threshold: 267\n        fraction: 0.03\n\n    use_only_main_island: false\n\n')
    
    f.write('MAGIC:\n    image_extractor:\n        type: "SlidingWindowMaxSum"\n        window_width: 5\n        apply_integration_correction: false\n\n')
    f.write('    charge_correction:\n        use: true\n        factor: 1.143\n\n')
    f.write('    magic_clean:\n        use_time: true\n        use_sum: true\n        picture_thresh: 6\n        boundary_thresh: 3.5\n        max_time_off: 4.5\n        max_time_diff: 1.5\n        find_hotpixels: true\n        pedestal_type: "from_extractor_rndm"\n\n')
    f.write('    muon_ring:\n        thr_low: 25\n        tailcut: [12, 8]\n        ring_completeness_threshold: 25\n\n')
    f.close()


def lists_and_bash_generator(particle_type, target_dir, MC_path, environment, focal_length):
    """
    This function creates the lists list_nodes_gamma_complete.txt and list_folder_gamma.txt with the MC file paths.
    After that, it generates a few bash scripts to link the MC paths to each subdirectory. 
    This bash script will be called later in the main() function below. 
    """
    
    process_name = target_dir.split("/")[-2:][0]+target_dir.split("/")[-2:][1]
    
    """
    Below we create the bash scripts that link the MC paths to each subdirectory. 
    """

    if not os.path.exists(f"{target_dir}/DL1/MC/{particle_type}/single_node"):
        os.mkdir(f"{target_dir}/DL1/MC/{particle_type}/single_node")

    os.system(f"ls {MC_path}/*simtel.gz > {target_dir}/DL1/MC/{particle_type}/single_node/list_dl0_ok.txt")
    
    """
    Below we create a bash script that applies lst1_magic_mc_dl0_to_dl1.py to all MC data files. 
    """
    
    number_of_nodes = len(glob.glob(MC_path+"/*simtel.gz"))
    number_of_nodes = number_of_nodes -1
    
    f = open(f"linking_MC_{particle_type}_paths_r.sh","w")
    f.write('#!/bin/sh\n\n')
    f.write("#SBATCH -p short\n")
    f.write("#SBATCH -J "+process_name+"\n")
    f.write(f"#SBATCH --array=0-{number_of_nodes}%50\n")
    f.write("#SBATCH -N 1\n\n")
    f.write("ulimit -l unlimited\n")
    f.write("ulimit -s unlimited\n")
    f.write("ulimit -a\n\n")

    f.write("export INPUTDIR="+target_dir+f"/DL1/MC/{particle_type}/single_node\n")
    f.write("SAMPLE_LIST=($(<$INPUTDIR/list_dl0_ok.txt))\n")
    f.write("SAMPLE=${SAMPLE_LIST[${SLURM_ARRAY_TASK_ID}]}\n\n")

    f.write("export LOG=$INPUTDIR/../dl0_to_dl1_${SLURM_ARRAY_TASK_ID}.log\n")
    f.write(f"conda run -n {environment} python lst1_magic_mc_dl0_to_dl1.py --input-file $SAMPLE --output-dir {target_dir}/DL1/MC/{particle_type}/single_node --config-file {target_dir}/config_step1.yaml --focal_length_choice {focal_length} >$LOG 2>&1")

    f.close()
    
    
    
    
    
def directories_generator(target_dir):
    """
    Here we create all subdirectories for a given workspace and target name.
    """
    
    ###########################################
    ##################### MC
    ###########################################
        
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)
        os.mkdir(target_dir+"/DL1")
        os.mkdir(target_dir+"/DL1/Observations")
        os.mkdir(target_dir+"/DL1/MC")
        os.mkdir(target_dir+"/DL1/MC/gammas")
        os.mkdir(target_dir+"/DL1/MC/gammadiffuse")
        os.mkdir(target_dir+"/DL1/MC/electrons")
        os.mkdir(target_dir+"/DL1/MC/protons")
        os.mkdir(target_dir+"/DL1/MC/helium")
    else:
        overwrite = input("Directory "+target_dir.split("/")[-1]+" already exists. Would you like to overwrite it? [only 'y' or 'n']: ")
        if overwrite == "y":
            os.system("rm -r "+target_dir)
            os.mkdir(target_dir)
            os.mkdir(target_dir+"/DL1")
            os.mkdir(target_dir+"/DL1/Observations")
            os.mkdir(target_dir+"/DL1/MC")
            os.mkdir(target_dir+"/DL1/MC/gammas")
            os.mkdir(target_dir+"/DL1/MC/gammadiffuse")
            os.mkdir(target_dir+"/DL1/MC/electrons")
            os.mkdir(target_dir+"/DL1/MC/protons")
            os.mkdir(target_dir+"/DL1/MC/helium")
        else:
            print("Directory not modified.")



def main():

    """ Here we read the config_general.yaml file and call the functions to generate the necessary directories, bash scripts and launching the jobs."""
    
    with open("config_general.yaml", "rb") as f:   # "rb" mode opens the file in binary format for reading
        config = yaml.safe_load(f)
        
    telescope_ids = list(config["mc_tel_ids"].values())
    target_dir = str(Path(config["directories"]["workspace_dir"]+config["directories"]["target_name"]))
    MC_gammas  = str(Path(config["directories"]["MC_gammas"]))
    MC_electrons = str(Path(config["directories"]["MC_electrons"]))
    MC_helium = str(Path(config["directories"]["MC_helium"]))
    MC_protons = str(Path(config["directories"]["MC_protons"]))
    MC_gammadiff = str(Path(config["directories"]["MC_gammadiff"]))
    focal_length = config["general"]["focal_length"]
    environment = config["general"]["environment_name"]
    
    
    print("***** Linking MC paths - this may take a few minutes ******")
    print("*** Reducing DL0 to DL1 data - this can take many hours ***")
    print("Process name: ",target_dir.split('/')[-2:][0]+target_dir.split('/')[-2:][1])
    print("To check the jobs submitted to the cluster, type: squeue -n",target_dir.split('/')[-2:][0]+target_dir.split('/')[-2:][1])
    
    directories_generator(target_dir) #Here we create all the necessary directories in the given workspace and collect the main directory of the target   
    config_file_gen(telescope_ids,target_dir)
    
    lists_and_bash_generator("gammas", target_dir, MC_gammas, environment, focal_length) #gammas
    lists_and_bash_generator("electrons", target_dir, MC_electrons, environment, focal_length) #electrons
    #lists_and_bash_generator("helium", target_dir, MC_helium, focal_length) #helium
    lists_and_bash_generator("protons", target_dir, MC_protons, environment, focal_length) #protons
    lists_and_bash_generator("gammadiffuse", target_dir, MC_gammadiff, environment, focal_length) #gammadiffuse
    
    #Here we do the MC DL0 to DL1 conversion:
    list_of_MC = glob.glob("linking_MC_*.sh")
    
    for run in list_of_MC:
        os.system(f"sbatch {run}")
                
if __name__ == "__main__":
    main()
    

    
    
    
    
