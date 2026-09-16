import os
from pathlib import Path

import pandas as pd
import numpy as np
from huggingface_hub import hf_hub_download
from PIL import Image
from onnxruntime import InferenceSession

from .interrogator import Interrogator
from . import dbimutils
from ..runtime import logger


class WaifuDiffusionInterrogator(Interrogator):
    def __init__(
            self,
            name: str,
            model_path='model.onnx',
            tags_path='selected_tags.csv',
            **kwargs
    ) -> None:
        super().__init__(name)
        self.model_path = model_path
        self.tags_path = tags_path
        self.kwargs = kwargs

    def download(self) -> tuple[os.PathLike, os.PathLike]:
        logger.info(f"Loading {self.name} model file from {self.kwargs['repo_id']}")

        model_path = Path(hf_hub_download(
            **self.kwargs, filename=self.model_path))
        tags_path = Path(hf_hub_download(
            **self.kwargs, filename=self.tags_path))
        return model_path, tags_path

    def load(self) -> None:
        model_path, tags_path = self.download()

        # only one of these packages should be installed at a time in any one environment
        # https://onnxruntime.ai/docs/get-started/with-python.html#install-onnx-runtime
        # TODO: remove old package when the environment changes?
        # from mikazuki.launch_utils import is_installed, run_pip
        # if not is_installed('onnxruntime'):
        #     package = os.environ.get(
        #         'ONNXRUNTIME_PACKAGE',
        #         'onnxruntime-gpu'
        #     )

        #     run_pip(f'install {package}', 'onnxruntime')

        # Load torch to load cuda libs built in torch for onnxruntime, do not delete this.

        

        # https://onnxruntime.ai/docs/execution-providers/
        # https://github.com/toriato/stable-diffusion-webui-wd14-tagger/commit/e4ec460122cf674bbf984df30cdb10b4370c1224#r92654958
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']

        self.model = InferenceSession(str(model_path), providers=providers)

        logger.info(f'Loaded {self.name} model from {model_path}')

        self.tags = pd.read_csv(tags_path)

    def interrogate(
        self,
        image: Image.Image
    ) -> tuple[
        dict[str, float],  # rating confidents
        dict[str, float]  # tag confidents
    ]:
        # init model
        if not hasattr(self, 'model') or self.model is None:
            self.load()

        # code for converting the image and running the model is taken from the link below
        # thanks, SmilingWolf!
        # https://huggingface.co/spaces/SmilingWolf/wd-v1-4-tags/blob/main/app.py

        # convert an image to fit the model
        _, height, _, _ = self.model.get_inputs()[0].shape

        # alpha to white
        rgba_image = image.convert('RGBA')
        new_image = Image.new('RGBA', rgba_image.size, 'WHITE')
        new_image.paste(rgba_image, mask=rgba_image)
        rgb_image = new_image.convert('RGB')
        rgb_array = np.asarray(rgb_image)

        # PIL RGB to OpenCV BGR
        bgr_array = rgb_array[:, :, ::-1]

        square_image = dbimutils.make_square(bgr_array, height)
        resized_image = dbimutils.smart_resize(square_image, height)
        resized_image = resized_image.astype(np.float32)
        model_input = np.expand_dims(resized_image, 0)

        # evaluate model
        input_name = self.model.get_inputs()[0].name
        label_name = self.model.get_outputs()[0].name
        confidents = np.asarray(self.model.run([label_name], {input_name: model_input})[0], dtype=np.float32)

        tags = self.tags[['name']].copy()
        tags['confidents'] = confidents[0]

        # first 4 items are for rating (general, sensitive, questionable, explicit)
        ratings = dict(tags[:4].values)

        # rest are regular tags
        tags = dict(tags[4:].values)

        return ratings, tags
