# %%
from pathlib import Path

from jwst_fourier.pipeline import Fourier1Pipeline, Fourier2Pipeline

input_file = Path(
    "data/01189/jw01189017001_06101_00001_nis_uncal.fits"
)
input_files = [input_file]

# %%
output_dir_parent = Path("results/test2_oof")
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

steps_stage2 = [
    "bkg_subtract",
    "assign_wcs",
    "flat_field",
    "photom",
    "resample",
    "oneoverf",
]

config_dict = {
    "oneoverf": {
        "save_results": True,
        "save_intermediate": True,
        "output_dir": str(output_dir_stage1),
    },
}

run_stage1 = False
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
        pipe2 = Fourier2Pipeline()
        pipe2.save_results = True
        pipe2.output_dir = str(output_dir_stage2)
        pipe2.photom.skip = True
        pipe2.resample.skip = True
        pipe2.run(stage1_files, step_list=steps_stage2, cfg_dict=config_dict)
