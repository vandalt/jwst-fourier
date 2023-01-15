from argparse import ArgumentParser
from pathlib import Path

import yaml

from jwst_fourier.pipeline import Fourier1Pipeline, Fourier2Pipeline

psr = ArgumentParser(description="Run Fourier imaging JWST reduction")
psr.add_argument(
    "config_file", type=str, help="YAML configuration file for pipeline script"
)

cli_args = psr.parse_args()
config_file = cli_args.config_file

with open(config_file, "r") as cfg:
    cfg_dict = yaml.safe_load(cfg)


def get_input_files(input_cfg):
    if isinstance(input_cfg, str):
        return [input_cfg]
    elif isinstance(input_cfg, list):
        return input_cfg
    else:
        raise TypeError("Unexpected type for input_file(s) config")


if "input_file" in cfg_dict and "input_files" not in cfg_dict:
    input_files = get_input_files(cfg_dict["input_file"])
elif "input_files" in cfg_dict and "input_file" not in cfg_dict:
    input_files = get_input_files(cfg_dict["input_files"])
elif "input_files" in cfg_dict and "input_file" in cfg_dict:
    raise ValueError("input_files and input_file cannot both be provided.")
else:
    raise ValueError("One of input_files or input file must be provided.")
input_files = [Path(f) for f in input_files]
output_dir_parent = Path(cfg_dict["output_dir_parent"])

output_dir_stage1 = output_dir_parent
output_dir_stage2 = output_dir_parent
if "stage1_subdir" in cfg_dict and cfg_dict["stage1_subdir"] is not None:
    output_dir_stage1 = output_dir_stage1 / cfg_dict["stage1_subdir"]
if "stage2_subdir" in cfg_dict and cfg_dict["stage2_subdir"] is not None:
    output_dir_stage2 = output_dir_stage2 / cfg_dict["stage2_subdir"]
output_dir_stage1.mkdir(exist_ok=True, parents=True)
output_dir_stage2.mkdir(exist_ok=True, parents=True)

if "steps" in cfg_dict:
    steps_stage1 = cfg_dict.get("steps")
else:
    steps_stage1 = cfg_dict.get("steps_stage1")
steps_stage2 = cfg_dict.get("steps_stage2")

if "step_config" in cfg_dict:
    stage1_config = cfg_dict.get("step_config")
else:
    stage1_config = cfg_dict.get("stage1_config")
if "stage2_config" not in cfg_dict and "step_config" in cfg_dict:
    stage2_config = cfg_dict.get("step_config")
else:
    stage2_config = cfg_dict.get("stage2_config")

run_stage1 = cfg_dict.get("run_stage1") or False
run_stage2 = cfg_dict.get("run_stage2") or False

for input_file in input_files:
    if run_stage1:
        pipe1 = Fourier1Pipeline()
        pipe1.save_results = True
        pipe1.output_dir = str(output_dir_stage1)
        pipe1.ipc.skip = True
        pipe1.run(str(input_file), step_list=steps_stage1, cfg_dict=stage1_config)

    if run_stage2:
        file_base = input_file.name
        stage1_files = []
        for suffix in ["rate", "rateints"]:
            stage1_file = str(output_dir_stage1 / file_base.replace("uncal", suffix))
            stage1_files.append(stage1_file)
        pipe2 = Fourier2Pipeline()
        pipe2.save_results = True
        pipe2.output_dir = str(output_dir_stage2)
        pipe2.photom.skip = True
        pipe2.resample.skip = True
        pipe2.run(stage1_files, step_list=steps_stage2, cfg_dict=stage2_config)
