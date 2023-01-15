from jwst import datamodels
from jwst.stpipe import Step

from . import one_over_f

__all__ = ["OneOverFStep"]


class OneOverFStep(Step):
    """
    OneOverFStep: Performs 1/f noise correction by computing a constant
    for each column from the input ramp data model.
    """

    class_alias = "oneoverf"

    spec = """
        outlier_map = str(default=None)
        iterative = boolean(default=False)
        save_intermediate = boolean(default=False)
        intermediate_output_subdir = str(default=None)
        mean_per_frame = boolean(default=False)
    """

    def process(self, input):
        try:
            with datamodels.RampModel(input) as input_model:

                # TODO: This raises warning about 0 when doing weight RMS calculation.
                # TODO: If want intermediate to save normally, should use data models and pass then here
                result = one_over_f.correct_oof(
                    input_model,
                    output_dir=self.output_dir,
                    outlier_map=self.outlier_map,
                    iterative=self.iterative,
                    save_intermediate=self.save_intermediate,
                    intermediate_output_subdir=self.intermediate_output_subdir,
                    mean_per_frame=self.mean_per_frame,
                )
        except ValueError:
            with datamodels.open(input) as input_model:

                # TODO: This raises warning about 0 when doing weight RMS calculation.
                # TODO: If want intermediate to save normally, should use data models and pass then here
                if not isinstance(input_model, datamodels.CubeModel):
                    self.log.warning(
                        "Stage 2 input is not a CubeModel. Skipping 1/f (OOF) correction."
                    )
                    return input_model
                result = one_over_f.correct_oof(
                    input_model,
                    output_dir=self.output_dir,
                    outlier_map=self.outlier_map,
                    iterative=self.iterative,
                    save_intermediate=self.save_intermediate,
                    intermediate_output_subdir=self.intermediate_output_subdir,
                    mean_per_frame=self.mean_per_frame,
                )

        result.meta.cal_step.oneoverf = "COMPLETE"

        return result


if __name__ == "__main__":
    # Open the uncal time series that needs 1/f correction
    exposurename = (
        "../scratch/results/stage1/jw01189017001_06101_00001_nis_saturation.fits"
    )
    outdir = "scratch/results/oof_test"

    step = OneOverFStep()
    step.save_results = True
    step.run(exposurename)
