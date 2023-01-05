# JWST Fourier Imaging Pipeline

Custom pipeline scripts to process kernel phase and AMI data in JWST pipeline stages 1 and 2.

## Steps and pipelines
<!-- TODO: Confirm recommended position after tests  -->

### Fourier1Pipeline

- `Fourier1Pipeline` is a subclass of `Detector1Pipeline`
- Includes all steps from detector1, but also an extra `OneOverFStep` (see section below)
- By default, 1/f correction is between `ipc` and `superbias`

### 1/f noise step (OneOverFStep)

- Custom pipeline step to correct 1/f noise
- Designed to process data cube inside stage 1 pipeline (4-D array)
- By default, this step should go between `ipc` and `superbias` steps in the `Fourier1Pipeline` (see previous section)
- Not implemented for MIRI
- Correction is done by subtracting an image stacked over integrations for each group, then computing a mean value for each column in the array
- For the FULL subarray, each amplificator is handled separately (column is split in 4)

## Scripts
Currently, the `scripts` directory only includes scripts I'm using to debug the pipeline and experiment with it (this section is mainly a reminder for myself). The `scripts` directory contains:

- `reduce_data.py` is a Python script that takes a YAML config file to order steps and set their configuration options
- `reduce_data_nb.py` is a notebook (Jupytext "percent" format) that does pretty much the same thing as the script, but the setup is done directly in Python in the first few cells of the notebook.
