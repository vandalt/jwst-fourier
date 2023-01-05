from argparse import ArgumentParser
from pathlib import Path

import yaml
from jwst.pipeline import Image2Pipeline

from jwst_fourier.pipeline import Fourier1Pipeline

psr = ArgumentParser(description="Run Fourier imaging JWST reduction")
psr.add_argument(
    "config_file", type=str, help="YAML configuration file for pipeline script"
)

cli_args = psr.parse_args()
config_file = cli_args.config_file

with open(config_file, "r") as cfg:
    cfg_dict = yaml.safe_load(cfg)

input_file = Path(cfg_dict["input_file"])
output_dir_parent = Path(cfg_dict["output_dir_parent"])

output_dir_stage1 = output_dir_parent
output_dir_stage2 = output_dir_parent
if "stage1_subdir" in cfg_dict and cfg_dict["stage1_subdir"] is not None:
    output_dir_stage1 = output_dir_stage1 / cfg_dict["stage1_subdir"]
if "stage2_subdir" in cfg_dict and cfg_dict["stage2_subdir"] is not None:
    output_dir_stage2 = output_dir_stage2 / cfg_dict["stage2_subdir"]
output_dir_stage1.mkdir(exist_ok=True, parents=True)
output_dir_stage2.mkdir(exist_ok=True, parents=True)

steps = cfg_dict.get("steps")
step_config = cfg_dict.get("step_config")

run_stage1 = cfg_dict.get("run_stage1") or False
run_stage2 = cfg_dict.get("run_stage2") or False

if run_stage1:
    pipe1 = Fourier1Pipeline()
    pipe1.save_results = True
    pipe1.output_dir = str(output_dir_stage1)
    pipe1.ipc.skip = True
    pipe1.run(str(input_file), step_list=steps, cfg_dict=step_config)

if run_stage2:
    file_base = input_file.name
    stage1_files = []
    for suffix in ["rate", "rateints"]:
        stage1_file = str(output_dir_stage1 / file_base.replace("uncal", suffix))
        stage1_files.append(stage1_file)
    pipe2 = Image2Pipeline()
    pipe2.save_results = True
    pipe2.output_dir = str(output_dir_stage2)
    pipe2.photom.skip = True
    pipe2.resample.skip = True
    pipe2.run(stage1_files)
