from pathlib import Path
import glob

from jwst.pipeline import Image2Pipeline
from jwst_fourier.pipeline import Fourier1Pipeline

input_file = Path(
    "/home/vandal/Documents/data/jwst-obs/01093/jw01093001001_03106_00002_nis_uncal.fits"
)

# %%
output_dir_parent = Path("results/commissioning")
output_dir_stage1 = output_dir_parent
output_dir_stage1.mkdir(exist_ok=True, parents=True)
output_dir_stage2 = output_dir_parent
output_dir_stage2.mkdir(exist_ok=True, parents=True)


# %%
steps = [
    "group_scale",
    "dq_init",
    "saturation",
    # "oneoverf",
    "superbias",
    "refpix",
    "linearity",
    "persistence",
    "dark_current",
    "jump",
    "ramp_fit",
    "gain_scale",
]

config_dict = {
    "oneoverf": {
        "save_results": True,
        "save_intermediate": True,
        "output_dir": str(output_dir_stage1),
    },
}

run_stage1 = True
run_stage2 = True

# %%
for input_file in input_files:
    if run_stage1:
        pipe1 = Fourier1Pipeline()
        pipe1.save_results = True
        pipe1.output_dir = str(output_dir_stage1)
        pipe1.ipc.skip = True
        pipe1.run(str(input_file), step_list=steps, cfg_dict=config_dict)

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
