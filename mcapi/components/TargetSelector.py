class TargetSelector:
    """
    In most commands where entities may be specified as an argument,
    it is possible to "target" one or more entities satisfying
    certain conditions. To target entities by condition,
    choose a target selector variable and, optionally,
    one or more target selector arguments to modify the conditions
    to be satisfied.

    Available identifiers:
        - p	    |= nearest player
        - a	    |= all players
        - r	    |= random player
        - s	    |= entity executing the command
        - e	    |= all entities

    Summary of target selector arguments:

        Selection by Position:
            Argument(s)	 |  Selection criteria   |  Example value
            _____________________________________________________

            x, y, z	     |  coordinate           |  (float, int) 7, +12.34, -0.1
            distance‌     |  distance	          |  (int, str) 8, 16, "8..16" (from 8 to 16)
            dx, dy, dz	 |  volume dimensions    |  (int) 1, 2, 0

        Selection by Scoreboard Values:
            Argument(s)	 |  Selection criteria   |  Example value
            _____________________________________________________

            scores	     |  scores               |  (dict) {myscore=10}, {foo=..15}
            *tag	     |  tag                  |  (str) has_tag, !hasnt_tag, "" (=has no tags)
            team	     |  team name            |  (str) in_team, !not_in_team, "" (=has no team)

        Selection by Traits:
            Argument(s)	 |  Selection criteria   |  Example value
            _____________________________________________________

            limit,sort‌   |  limit                |  (str and int) sort=(nearest|furthest|random|arbitrary) limit= (int)
            level‌        |  experience level     |  (int, str) 8, 16, "8..16" (from 8 to 16)
            gamemode‌     |  game mode            |  (str) gamemode=(spectator‌|adventure|creative|survival), !survival
            name	     |  entity name          |  (str) Johnson, !Johnson
            x_rotation   |  vertical rotation    |  (int, str) 8, 16, "8..16" (from 8 to 16)
            y_rotation   |  horizontal rotation  |  (int, str) 8, 16, "8..16" (from 8 to 16)
            type	     |  entity type          |  (str) pig, mod:modded_mob, !pig
            nbt‌          |  nbt                  |  (dict, object) {OnGround:true}, [class] NBT()
            advancements‌ |  advancements         |  (dict) {story/follow_ender_eye=true}
            predicate    |  predicate            |  (str) example:test_predicate

    *can be a list of the value

    You can read in-depth about target selectors at:
        https://minecraft.fandom.com/wiki/Commands#Target_selectors
    """

    argument_list = [
        "x",
        "y",
        "z",
        "dx",
        "dy",
        "dz",
        "distance",
        "scores",
        "tag",
        "team",
        "limit",
        "sort‌",
        "level‌",
        "gamemode‌",
        "name",
        "x_rotation",
        "y_rotation",
        "type",
        "nbt‌",
        "advancements‌",
        "predicate",
    ]

    def __init__(self, identifier: str, arguments: dict = None):

        if identifier not in ["p", "a", "r", "s", "e"]:
            raise IncorrectTargetSelectorIdentifier(
                f"The TargetSelector identifier must be either P, A, R, S or E"
            )

        self.id = identifier

        if not isinstance(arguments, dict) and arguments is not None:
            raise IncorrectTargetSelectorArgumentsType(
                f"The TargetSelector arguments must be passed as a dictionnary"
            )

        self.arguments = arguments

    def __str__(self):
        buff = ""

        if self.arguments is not None:

            for key in self.arguments:

                if key not in self.argument_list:
                    raise InvalidTargetSelectorArgumentKey(
                        f'The key "{key}" is not a valid argument type for a selector'
                    )

                if isinstance(self.arguments[key], list):
                    for element in self.arguments[key]:
                        buff += f"{key}={element},"
                else:
                    buff += f"{key}={self.arguments[key]},"

            if buff != "":
                buff = buff[:-1]

        return f"@{self.id}[{buff}]"


class IncorrectTargetSelectorIdentifier(Exception):
    pass


class IncorrectTargetSelectorArgumentsType(Exception):
    pass


class InvalidTargetSelectorArgumentKey(Exception):
    pass
