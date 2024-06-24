## IRFs for LSTs

1) Install MCP following the tutorial here: https://github.com/ranieremenezes/magic-cta-pipe/tree/master 

2) create a directory in your workspace. Let's say:
   
   mkdir 3LST_PMT

3) Copy the **config_general.yaml**, **lst1_magic_mc_dl0_to_dl1.py**, and **setting_up_config_and_dir.py** to this directory, modifying the configuration file as you wish. For deeper configuration changes, you will have to modify the first function of the file setting_up_config_and_dir.py

### DL0 to DL1

Simply run the following command in your working environment:

```
python setting_up_config_and_dir.py
```

You can then check the log files in the directory pointsource/DL1/MC/gammas/. Each job will take less than 10 min to run.

Now we can split the proton sample into training and testing (be sure that the scripts **spliting_train_test.py** is in the working directory):

```
python spliting_train_test.py
```

Once it is done, we can compute the stereo parameters (be sure that the scripts **stereo_events.py** and **lst1_magic_stereo_reco.py** are in the working directory):

```
python stereo_events.py
```

We finish the DL1 analysis by merging the stereo files (**merging_runs.py** and **merge_hdf_files.py** must be in the working directory):

```
python merging_runs.py
```

Once we have the DL1 stereo parameters for all real and MC data, we can train the Random Forest (**RF.py** and **lst1_magic_train_rfs.py** must be in the working directory):

```
python RF.py
```

This script creates the file config_RF.yaml with several parameters related to the energy regressor, disp regressor, and event classifier, and then computes the RF (energy, disp, and classifier) based on the merged-stereo MC diffuse gammas and training proton samples by calling the script lst1_magic_train_rfs.py. The results are saved in [...]/DL1/MC/RFs.

### DL1 to DL2

Once it is done, we can finally convert our DL1 stereo files into DL2 by running:

```
python DL1_to_DL2.py
```

This script runs lst1_magic_dl1_stereo_to_dl2.py on all DL1 stereo files, which applies the RFs saved in [...]/DL1/MC/RFs to stereo DL1 data (real and test MCs) and produces DL2 real and MC data. The results are saved in [...]/DL2/Observations and [...]/DL2/MC.

Finally, we can run the IRFs and diagnostic plots (**IRF.py**, **diagnostic.py**, **lst1_magic_create_irf.py**, and **lst_magic_diagnostic.py** must be in the working directory):

```
python IRF.py
```

```
python diagnostic.py
```

The IRFs are saved at TARGET_NAME/IRF, while all diagnostic plots will be saved in the directory TARGET_NAME (defined in the config_general.yaml file).
