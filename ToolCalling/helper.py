import json
from typing import Callable


def get_fn_signature(fn: Callable) -> dict:
    """
    Generate the signature of a given function.

    :param fn: The function whose signature needs to be extracted.

    :return: A dictionary containing the function's name, description, and parameters types.
    """
    fn_signature = {
        "name": fn.__name__,
        "description": fn.__doc__,
        "parameters": {"properties": {}}
    }

    schema = {k: {"type": v.__name__} for k, v in fn.__annotations__.items()}
    fn_signature["parameters"]["properties"] = schema
    return fn_signature


def validate_arguments(tool_call: dict, tool_signature: dict) -> dict:
    """
    Validates and converts arguments in the input dictionary to match the expected types.

    :param tool_call: A dictionary containing the arguments passed to the tool.
    :param tool_signature: The expected function signature and parameter types.

    :return: The tool call dictionary with the arguments converted to the correct types if necessary.
    """
    properties = tool_signature["parameters"]["properties"]

    type_mapping = {
        "str": str,
        "int": int,
        "float": float,
        "bool": bool
    }

    for arg_name, arg_value in tool_call["arguments"].items():
        expected_type = properties[arg_name]["type"]

        if not isinstance(arg_value, type_mapping[expected_type]):
            tool_call["arguments"][arg_name] = type_mapping[expected_type](arg_value)

    return tool_call


class Tool:
    """
    A class representing a Tool that wraps a function and its signature.

    Attributes:
          name: The name of the tool (function).
          fn: The function that the tool represents.
          fn_signature: JSON string representation of the function's signature.
    """

    def __init__(self, name: str, fn: Callable, fn_signature: str):
        self.name = name
        self.fn = fn
        self.fn_signature = fn_signature

    def __str__(self):
        return self.fn_signature

    def run(self, **kwargs):
        """
        Executes the tool (function) with provided arguments.

        :param kwargs: Keyword arguments passed to the function.

        :return: The result of the function call.
        """
        return self.fn(**kwargs)


def tool(fn: Callable):
    """
    A decorator that wraps a function into a Tool object.

    :param fn: The function to be wrapped.

    :return: A Tool object containing the function, its name, and its signature.
    """
    def wrapper():
        fn_signature = get_fn_signature(fn)
        return Tool(name=fn_signature.get("name"),
                    fn=fn,
                    fn_signature=json.dumps(fn_signature))
    return wrapper()

