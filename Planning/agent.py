import json
from colorama import Fore
import aisuite as ai

from ToolCalling.helper import Tool,validate_arguments


BASE_SYSTEM_PROMPT = ""


class ReactAgent:
    """
    A class that represents an agent using the ReAct logic that interacts with tools to process
    user inputs, make decisions, and execute tool calls. The agent can run interactive sessions,
    collect tool signatures, and process multiple tool calls in a given round of interaction.

    Attributes:
        client: A LLM client used to handle model-based completions.
        model: The name of the model used for generating responses.
        tools: A list of Tool instances available for execution.
        tools_dict: A dictionary mapping toll names to their corresponding Tool instances.
    """

    def __init__(self,
                 tools: Tool | list[Tool],
                 model: str = "gpt-40-mini",
                 system_prompt: str = BASE_SYSTEM_PROMPT,):
        self.client = ai.Client()
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools if isinstance(tools, list) else [tools]
        self.tools_dict = {tool.name: tool for tool in tools}

    def add_tool_signatures(self) -> str:
        """
        Collects the function signatures of all available tools.

        :return: A string containing the function signatures of all tools in JSON format.
        """
        return "".join([tool.fn_signature for tool in self.tools])

    def process_tool_calls(self, tool_calls_content: list) -> dict:
        """
        Processes each tool call, validates arguments, execute the tools, and collect results.

        :param tool_calls_content: List of strings, each representing a tool call in JSON format.

        :return: A dictionary where the keys are tool call IDs and values are the results from the tools.
        """
        observations = {}
        for tool_call_str in tool_calls_content:
            tool_call = json.loads(tool_call_str)
            tool_name = tool_call["name"]
            tool = self.tools_dict[tool_name]

            print(Fore.GREEN + f"\nUsing Tool: {tool_name}")

            # validate and execute the tool call
            validated_tool_call = validate_arguments(
                tool_call, json.loads(tool.fn_signature)
            )
            print(Fore.GREEN + f"\nTool Call dict: \n{validated_tool_call}")

            result = tool.run(**validated_tool_call["arguments"])
            print(Fore.GREEN + f"\nTool Result: \n{result}")

            # Store the result using the tool call ID
            observations[validated_tool_call["id"]] = result
        return observations

    def run(self,
            user_msg: str,
            max_rounds: int = 10):
        """

        :param user_msg:
        :param max_rounds:
        :return:
        """





