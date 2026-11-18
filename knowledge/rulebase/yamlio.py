"""Strict YAML reading and writing for rule records.

Plain YAML silently lets a later duplicate key override an earlier one. For records whose history
must be trustworthy that is dangerous, so duplicate keys are an error here.
"""

from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode


class StrictLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys."""

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Any, Any]:
        seen: set[Any] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=True)
            if key in seen:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"duplicate key {key!r}",
                    key_node.start_mark,
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


class YamlError(ValueError):
    """The text is not valid (strict) YAML."""


def load_yaml_text(text: str) -> Any:
    try:
        return yaml.load(text, Loader=StrictLoader)
    except yaml.YAMLError as error:
        raise YamlError(str(error).replace("\n", " ")) from error


def dump_yaml(data: Any) -> str:
    """Stable, human-readable output with LF line endings."""
    return yaml.safe_dump(
        data, sort_keys=False, allow_unicode=True, default_flow_style=False, width=100
    )
