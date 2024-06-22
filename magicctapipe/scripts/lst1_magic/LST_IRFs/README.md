## IRFs for LSTs

1) create a directory in your workspace. Let's say:
   
   mkdir 3LST_PMT

2) Copy the **config_general.yaml**, **lst1_magic_mc_dl0_to_dl1.py**, and **setting_up_config_and_dir.py** to this directory, modifying the configuration file as you wish. For deeper configuration changes, you will have to modify the first function of the file setting_up_config_and_dir.py

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
