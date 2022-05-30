from distutils.command.build import build


def sanitize_very_strict(str):
    return "".join(
        c
        for c in str
        if c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890"
    )