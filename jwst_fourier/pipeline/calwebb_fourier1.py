import logging

from jwst import datamodels
from jwst.pipeline import Detector1Pipeline

from ..oneoverf import oneoverf_step

__all__ = ["Fourier1Pipeline"]


# Define logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Fourier1Pipeline(Detector1Pipeline):

    class_alias = "calwebb_fourier1"

    spec = """

    """

    _added_steps = {"oneoverf": oneoverf_step.OneOverFStep}

    step_defs = {**Detector1Pipeline.step_defs, **_added_steps}

    def run(self, *args, step_list=None, cfg_dict=None):
        all_args = (*args, step_list, cfg_dict)
        super().run(*all_args)

    def process(self, input, step_list, cfg_dict):

        log.info(f"Starting {self.class_alias} ...")

        if cfg_dict is not None:
            self.apply_cfg_dict(cfg_dict)

        # open the input as a RampModel
        input = datamodels.RampModel(input)

        # propagate output_dir to steps that might need it
        self.dark_current.output_dir = self.output_dir
        self.ramp_fit.output_dir = self.output_dir

        instrument = input.meta.instrument.name
        if instrument == "MIRI":

            # process MIRI exposures;
            # the steps are in a different order than NIR
            log.debug("Processing a MIRI exposure")
        else:

            # process Near-IR exposures
            log.debug("Processing a Near-IR exposure")

        step_list = step_list or self.get_default_steps(instrument)

        for step_name in step_list:
            if step_name in ("ramp_fit", "gain_scale"):
                break
            if step_name == "persistence" and instrument == "NIRSPEC":
                log.info("Skipping persistence step for NIRSPEC")
                continue
            step = getattr(self, step_name)
            input = step(input)

        # save the corrected ramp data, if requested
        if self.save_calibrated_ramp:
            self.save_model(input, "ramp")

        # apply the ramp_fit step
        # This explicit test on self.ramp_fit.skip is a temporary workaround
        # to fix the problem that the ramp_fit step ordinarily returns two
        # objects, but when the step is skipped due to `skip = True`,
        # only the input is returned when the step is invoked.
        if self.ramp_fit.skip or "ramp_fit" not in step_list:
            input = self.ramp_fit(input)
            ints_model = None
        else:
            input, ints_model = self.ramp_fit(input)

        if "gain_scale" in step_list:
            # apply the gain_scale step to the exposure-level product
            if input is not None:
                self.gain_scale.suffix = "gain_scale"
                input = self.gain_scale(input)
            else:
                log.info("NoneType returned from ramp_fit.  Gain Scale step skipped.")

            # apply the gain scale step to the multi-integration product,
            # if it exists, and then save it
            if ints_model is not None:
                self.gain_scale.suffix = "gain_scaleints"
                ints_model = self.gain_scale(ints_model)

        if ints_model is not None:
            self.save_model(ints_model, "rateints")

        # setup output_file for saving
        self.setup_output(input)

        log.info(f"... ending {self.class_alias}")

        return input

    def get_default_steps(self, instrument):
        if instrument == "MIRI":
            # NOTE: No custom steps implemented for MIRI. Just does what calwebb_detector1 would do
            instrument_specific_list = [
                "group_scale",
                "dq_init",
                "saturation",
                "ipc",
                "firstframe",
                "lastframe",
                "reset",
                "linearity",
                "rscd",
                "dark_current",
                "refpix",
            ]
        else:
            instrument_specific_list = [
                "group_scale",
                "dq_init",
                "saturation",
                "ipc",
                "oneoverf",
                "superbias",
                "refpix",
                "linearity",
            ]
            if instrument != "NIRSPEC":
                instrument_specific_list.append("persistence")
            instrument_specific_list.append("dark_current")

        generic_list = ["jump", "ramp_fit", "gain_scale"]

        return instrument_specific_list + generic_list

    def apply_cfg_dict(self, cfg_dict):
        for step_name in self.step_defs:
            step_cfg = cfg_dict.get(step_name)
            if step_cfg is None:
                continue
            step = getattr(self, step_name)
            for k, v in step_cfg.items():
                setattr(step, k, v)
