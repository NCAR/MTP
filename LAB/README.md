Both src\MTPcontrol.py and src\MTPviewer.py reference a project configuration directory with the following components:
```
  <project>\  <- project name
    config\
      ascii_parms  <- used to parse IWG packet
      config.Mtph
      proj.yml
      Production\
        setup_rf##.yml  <- one per flight, used for post-processing
    logs\
    Raw\
    RC\  <- contains project RCF files
```
This directory contains a LAB project setup suitable for testing. For a field project, you can copy this dir to the project area, then:
 * Copy the ascii_parms file from the RAF proj dir for the project
 * Create/update config/proj.yml. Use the sample_proj.yml as a starting point.
   * Edit the PROJECT and FLIGHT
 * Obtain RC\ files from the instrument PI and copy them into the RC\ dir

