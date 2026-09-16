from typing import Literal, TypeAlias
from invokeai.invocation_api import BaseInvocation, UIComponent, InvocationContext, invocation, InputField
from invokeai.invocation_api import BaseInvocationOutput, invocation_output, OutputField
from invokeai.app.invocations.primitives import ImageField
from ..tagger.interrogator import interrogate_image
from ..tagger.model import available_interrogators
from ..runtime import logger


AvailableModel: TypeAlias = Literal[tuple(available_interrogators)] # type: ignore


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
class Wd14Tagger(BaseInvocation):
    """tagging images with wd14 models"""

    image: ImageField = InputField(
        description="the image to tagger"
    )
    interrogator: AvailableModel = InputField(
        default="wd-swinv2-v3",
        description="the model to tagger image"
    )
    threshold: float = InputField(
        default=0.35,
        description="threshold"
    )
    additional_tags: str = InputField(
        default="",
        description="enter additional tags split by comma",
        ui_component=UIComponent.Textarea
    )
    exclude_tags: str = InputField(
        default="",
        description="enter exclude tags split by comma",
        ui_component=UIComponent.Textarea
    )
    replace_underscore: Literal["ON", "OFF"] = InputField(
        default="ON",
        description="replace underscore to space"
    )
    replace_underscore_excludes: str = InputField(
        default="0_0, (o)_(o), +_+, +_-, ._., <o>_<o>, <|>_<|>, =_=, >_<, 3_3, 6_9, >_o, @_@, ^_^, o_o, u_u, x_x, |_|, ||_||",
        description="enter replace tags split by comma",
        ui_component=UIComponent.Textarea
    )
    escape_tag: Literal["ON", "OFF"] = InputField(
        default="ON",
        description="escape brackets of tagger result"
    )
    unload_model_after_running: Literal["ON", "OFF"] = InputField(
        default="ON",
        description="unload model after running Tagger"
    )


    def invoke(self, context: InvocationContext) -> WD14PromptOutput:
        logger.info("Tagging Image")
        image = context.images.get_pil(self.image.image_name)
        interrogator_name = self.interrogator or "wd-swinv2-v3"
        interrogator = available_interrogators[interrogator_name]
        threshold = self.threshold or 0.35
        additional_tags = self.additional_tags or ""
        exclude_tags = self.exclude_tags or ""
        replace_underscore_excludes = self.replace_underscore_excludes or ""
        replace_underscore = self.replace_underscore == "ON"
        escape_tag = self.escape_tag == "ON"
        unload_model_after_running = self.unload_model_after_running == "ON"

        prompt = interrogate_image(
            image=image,
            interrogator=interrogator,
            threshold=threshold,
            additional_tags=additional_tags,
            exclude_tags=exclude_tags,
            sort_by_alphabetical_order=False,
            add_confident_as_weight=False,
            replace_underscore=replace_underscore,
            replace_underscore_excludes=replace_underscore_excludes,
            escape_tag=escape_tag,
            unload_model_after_running=unload_model_after_running
        )

        plain_tags = ', '.join(prompt)
        logger.info("Tagging Image Done")
        print("====================================================================================================")
        print(f"Prompt:\n{plain_tags}")
        print("====================================================================================================\n")
        return WD14PromptOutput(prompt=plain_tags)
