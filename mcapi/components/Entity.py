from typing import Union

from .NBT import NBT
from .TargetSelector import TargetSelector


class Entity:
    """
    Must be a player name, a target selector or a UUID.

    Each entity argument may place limits on the number of
    entities (single/multiple) selected or the type of entities
    (player/any entity) selected.

    e.g:
        - Player
        - 0123
        - @e
        - @e[type=foo]
        - dd12be42-52a9-4a91-a8a1-11c01849e498

    An instance of this class represents an existing unique entity, or a group of unique entities.
    """

    def __init__(self, descriptor: Union[TargetSelector, str]):

        if not isinstance(descriptor, TargetSelector) and not isinstance(
            descriptor, str
        ):
            raise IncorrectEntityDescriptorType(
                f"The Entity descriptor must either be a TargetSelector instance or a string"
            )

        if not descriptor:
            raise ValueError(
                f"The descriptor provided to to TargetSelector was empty or invalid"
            )

        self.descriptor = str(descriptor)

    def __str__(self):
        return f"{self.descriptor}"


class IncorrectEntityDescriptorType(Exception):
    pass
