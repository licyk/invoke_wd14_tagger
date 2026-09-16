# from https://github.com/toriato/stable-diffusion-webui-wd14-tagger
import re

from PIL import Image

from ..runtime import logger

tag_escape_pattern = re.compile(r'([\\()])')


class Interrogator:
    @staticmethod
    def postprocess_tags(
            tags: dict[str, float],
            threshold=0.35,
            additional_tags: list[str] | None = None,
            exclude_tags: list[str] | None = None,
            sort_by_alphabetical_order=False,
            add_confident_as_weight=False,
            replace_underscore=False,
            replace_underscore_excludes: list[str] | None = None,
            escape_tag=False
    ) -> dict[str, float]:
        if additional_tags is None:
            additional_tags: list[str] = []
        if exclude_tags is None:
            exclude_tags: list[str] = []
        if replace_underscore_excludes is None:
            replace_underscore_excludes: list[str] = []

        for t in additional_tags:
            tags[t] = 1.0

        # those lines are totally not "pythonic" but looks better to me
        tags = {
            t: c

            # sort by tag name or confident
            for t, c in sorted(
                tags.items(),
                key=lambda i: i[0 if sort_by_alphabetical_order else 1],
                reverse=not sort_by_alphabetical_order
            )

            # filter tags
            if (
                c >= threshold
                and t not in exclude_tags
            )
        }

        new_tags = []
        for tag in list(tags):
            new_tag = tag

            if replace_underscore and tag not in replace_underscore_excludes:
                new_tag = new_tag.replace('_', ' ')

            if escape_tag:
                new_tag = tag_escape_pattern.sub(r'\\\1', new_tag)

            if add_confident_as_weight:
                new_tag = f'({new_tag}:{tags[tag]})'

            new_tags.append((new_tag, tags[tag]))
        tags = dict(new_tags)

        return tags

    def __init__(self, name: str) -> None:
        self.name = name

    def load(self):
        raise NotImplementedError()

    def unload(self) -> bool:
        unloaded = False

        if hasattr(self, 'model') and self.model is not None:
            del self.model
            unloaded = True
            logger.info(f'Unloaded {self.name}')

        if hasattr(self, 'tags'):
            del self.tags

        return unloaded

    def interrogate(
        self,
        image: Image.Image
    ) -> tuple[
        dict[str, float],  # rating confidents
        dict[str, float]  # tag confidents
    ]:
        raise NotImplementedError()


def split_str(s: str, separator: str = ',') -> list[str]:
    return [x.strip() for x in s.split(separator) if x]


def interrogate_image(
    image: Image.Image,
    interrogator: Interrogator,
    threshold: float,
    additional_tags: str,
    exclude_tags: str,
    sort_by_alphabetical_order: bool,
    add_confident_as_weight: bool,
    replace_underscore: bool,
    replace_underscore_excludes: str,
    escape_tag: bool,
    unload_model_after_running: bool
) -> dict[str, float]:
    postprocess_opts = (
        threshold,
        split_str(additional_tags),
        split_str(exclude_tags),
        sort_by_alphabetical_order,
        add_confident_as_weight,
        replace_underscore,
        split_str(replace_underscore_excludes),
        escape_tag
    )

    _, tags = interrogator.interrogate(image)
    processed_tags = Interrogator.postprocess_tags(
        tags,
        *postprocess_opts
    )

    if unload_model_after_running:
        interrogator.unload()

    return processed_tags