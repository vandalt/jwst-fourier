from collections import defaultdict
import os.path as op

from jwst import datamodels
from jwst.pipeline import Image2Pipeline
from jwst.associations.load_as_asn import LoadAsLevel2Asn

from ..oneoverf import oneoverf_step

__all__ = ["Fourier2Pipeline"]


class Fourier2Pipeline(Image2Pipeline):

    class_alias = "calwebb_fourier2"

    spec = """

    """

    _added_steps = {"oneoverf": oneoverf_step.OneOverFStep}

    step_defs = {**Image2Pipeline.step_defs, **_added_steps}

    def run(self, *args, step_list=None, cfg_dict=None):
        all_args = (*args, step_list, cfg_dict)
        super().run(*all_args)

    def process(self, input, step_list, cfg_dict):

        self.log.info('Starting calwebb_image2 ...')

        if cfg_dict is not None:
            self.apply_cfg_dict(cfg_dict)

        step_list = step_list or self.get_default_steps()

        # Retrieve the input(s)
        asn = LoadAsLevel2Asn.load(input, basename=self.output_file)

        # Each exposure is a product in the association.
        # Process each exposure.
        results = []
        for product in asn['products']:
            self.log.info('Processing product {}'.format(product['name']))
            if self.save_results:
                self.output_file = product['name']
            try:
                getattr(asn, 'filename')
            except AttributeError:
                asn.filename = "singleton"

            result = self.process_exposure_product(
                step_list,
                product,
                asn['asn_pool'],
                op.basename(asn.filename)
            )

            # Save result
            suffix = 'cal'
            if isinstance(result, datamodels.CubeModel):
                suffix = 'calints'
            result.meta.filename = self.make_output_path(suffix=suffix)
            results.append(result)

        self.log.info('... ending calwebb_image2')

        self.output_use_model = True
        self.suffix = False
        return results

    def process_exposure_product(
            self,
            step_list,
            exp_product,
            pool_name=' ',
            asn_file=' '
    ):
        """Process an exposure found in the association product

        Parameters
        ---------
        exp_product: dict
            A Level2b association product.

        pool_name: str
            The pool file name. Used for recording purposes only.

        asn_file: str
            The name of the association file.
            Used for recording purposes only.
        """
        # Find all the member types in the product
        members_by_type = defaultdict(list)
        for member in exp_product['members']:
            members_by_type[member['exptype'].lower()].append(member['expname'])

        # Get the science member. Technically there should only be
        # one. We'll just get the first one found.
        science = members_by_type['science']
        if len(science) != 1:
            self.log.warning(
                'Wrong number of science files found in {}'.format(
                    exp_product['name']
                )

            )
            self.log.warning('    Using only first one.')
        science = science[0]

        self.log.info('Working on input %s ...', science)
        if isinstance(science, datamodels.DataModel):
            input = science
        else:
            input = datamodels.open(science)

        # Record ASN pool and table names in output
        input.meta.asn.pool_name = pool_name
        input.meta.asn.table_name = asn_file

        # Do background processing, if necessary
        if "bkg_subtract" in step_list and len(members_by_type['background']) > 0:

            # Setup for saving
            self.bkg_subtract.suffix = 'bsub'
            if isinstance(input, datamodels.CubeModel):
                self.bkg_subtract.suffix = 'bsubints'

            # Backwards compatibility
            if self.save_bsub:
                self.bkg_subtract.save_results = True

            # Call the background subtraction step
            input = self.bkg_subtract(input, members_by_type['background'])

        if "assign_wcs" in step_list:
            input = self.assign_wcs(input)
        if "flat_field" in step_list:
            input = self.flat_field(input)
        if "photom" in step_list:
            input = self.photom(input)

        # Resample individual exposures, but only if it's one of the
        # regular 2D science image types
        if "resample" in step_list and input.meta.exposure.type.upper() in self.image_exptypes and \
                len(input.data.shape) == 2:
            self.resample.save_results = self.save_results
            self.resample.suffix = 'i2d'
            # TODO: Should resample result be set to input?
            # It was not in Image2pipeline... Usually skipping for AMI anyway
            self.resample(input)

        if "oneoverf" in step_list:
            input = self.oneoverf(input)

        # That's all folks
        self.log.info(
            'Finished processing product {}'.format(exp_product['name'])
        )
        return input

    def get_default_steps(self):
        step_list = [
            "bkg_subtract",
            "assign_wcs",
            "flat_field",
            "photom",
            "resample",
        ]
        return step_list

    def apply_cfg_dict(self, cfg_dict):
        for step_name in self.step_defs:
            step_cfg = cfg_dict.get(step_name)
            if step_cfg is None:
                continue
            step = getattr(self, step_name)
            for k, v in step_cfg.items():
                setattr(step, k, v)
