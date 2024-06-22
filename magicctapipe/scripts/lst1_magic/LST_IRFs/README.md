## IRFs for LSTs

1) create a directory in your workspace. Let's say:
   
   mkdir 3LST_PMT

2) Copy the config_general.yaml, lst1_magic_mc_dl0_to_dl1.py, and setting_up_config_and_dir.py to this directory, modifying the configuration file as you wish. For deeper configuration changes, you will have to modify the first function of the file setting_up_config_and_dir.py

### DL0 to DL1

Simply run the following command in your working environment:

```
python setting_up_config_and_dir.py
```

You can then check the log files in the directory pointsource/DL1/MC/gammas/. Each job will take less than 10 min to run.

Now we can split the proton sample into training and testing and then merge the runs for each particle:

```
python merging_runs_and_spliting_training_samples.py
```

