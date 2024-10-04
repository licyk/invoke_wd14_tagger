from typing import Literal, Optional
from invokeai.invocation_api import BaseInvocation, UIComponent, InvocationContext, invocation, InputField
from invokeai.invocation_api import BaseInvocationOutput, invocation_output, OutputField
from invokeai.app.invocations.primitives import ImageField
from invokeai.backend.util.logging import InvokeAILogger
from ..interrogator import available_interrogators, interrogate_image
from ..utils import setup_onnxruntime



logger = InvokeAILogger.get_logger(name='InvokeAI-WD14-Tagger')
logger.info("Loading WD1.4 Tagger Node")
setup_onnxruntime()
WD14_MODEL_TYPES = Optional[Literal[tuple(available_interrogators)]]



@invocation_output('wd14_prompt_string_output')
class WD14PromptOutput(BaseInvocationOutput):
    """output prompt processed by wd1.4 tagger"""

    prompt: str = OutputField(description="tagger image to prompt")


@invocation(
    "wd1.4_tagger",
    title="WD1.4 Tagger",
    tags=["image", "tagger", "wd1.4"],
    category="image",
    version="1.0.0",
)
class WD14_TAGGER(BaseInvocation):
    """tagging images with wd14 models"""

    image: ImageField = InputField(
        description="the image to tagger"
    )
    interrogator: WD14_MODEL_TYPES = InputField( # type: ignore
        default="wd-swinv2-v3", 
        description="the model to tagger image"
    )
    threshold: Optional[float] = InputField(
        default=0.35,
        description="threshold"
    )
    additional_tags: Optional[str] = InputField(
        default="",
        description="enter additional tags split by comma",
        ui_component=UIComponent.Textarea
    )
    exclude_tags: Optional[str] = InputField(
        default="",
        description="enter exclude tags split by comma",
        ui_component=UIComponent.Textarea
    )
    replace_underscore: Optional[Literal["ON", "OFF"]] = InputField(
        default="ON",
        description="replace underscore to space"
    )
    replace_underscore_excludes: Optional[str] = InputField(
        default="0_0, (o)_(o), +_+, +_-, ._., <o>_<o>, <|>_<|>, =_=, >_<, 3_3, 6_9, >_o, @_@, ^_^, o_o, u_u, x_x, |_|, ||_||",
        description="enter replace tags split by comma",
        ui_component=UIComponent.Textarea
    )
    escape_tag: Optional[Literal["ON", "OFF"]] = InputField(
        default="ON",
        description="escape brackets of tagger result"
    )
    unload_model_after_running: Optional[Literal["ON", "OFF"]] = InputField(
        default="ON",
        description="unload model after running Tagger"
    )


    def invoke(self, context: InvocationContext) -> WD14PromptOutput:
        logger.info("Tagging Image")
        image = context.images.get_pil(self.image.image_name)
        interrogator = available_interrogators[self.interrogator]
        replace_underscore = True if self.replace_underscore == "ON" else False
        escape_tag = True if self.escape_tag == "ON" else False
        unload_model_after_running = True if self.unload_model_after_running == "ON" else False

        prompt = interrogate_image(
            image=image,
            interrogator=interrogator,
            threshold=self.threshold,
            additional_tags=self.additional_tags,
            exclude_tags=self.exclude_tags,
            sort_by_alphabetical_order=False,
            add_confident_as_weight=False,
            replace_underscore=replace_underscore,
            replace_underscore_excludes=self.replace_underscore_excludes,
            escape_tag=escape_tag,
            unload_model_after_running=unload_model_after_running
        )

        plain_tags = ', '.join(prompt)
        logger.info("Tagging Image Done")
        print("====================================================================================================")
        print(f"Prompt:\n{plain_tags}")
        print("====================================================================================================\n")
        return WD14PromptOutput(prompt=plain_tags)



logger.info("Load WD1.4 Tagger Node Done")