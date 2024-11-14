import re
from pathlib import Path


# decorators

def _check_version(func):
    def wrapper(*args, **kwargs):
        name = args[0] if args else kwargs.get('name', '')

        if len(re.findall(r"_v\d+", name)) != 1:
            raise ValueError(f"Invalid number of versions within name: {name}. "
                             "Name must contain one version.")

        return func(*args, **kwargs)

    return wrapper


# functions


@_check_version
def insert_layer(name: str, layer: str) -> str:
    return re.sub(r"(_v\d+)", f"_{layer}\\1", name)


def get_name_from_filepath(filepath: str) -> str:
    return Path(filepath).with_suffix('').name


# if __name__ == "__main__":
#     s = "sh000_00_track_v001.abc"
#     print(insert_layer(s, "geo"))
