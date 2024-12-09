import json
import aisuite as ai
from colorama import Fore
from dotenv import load_dotenv, find_dotenv

from helper import Tool, validate_arguments
from utils.completions import build_prompt_structure, ChatHistory, completions_create, update_chat_history
from utils.extraction import extract_tag_content


_ = load_dotenv(find_dotenv())


TOOL_SYSTEM_PROMPT = """
You are a function calling AI model. You are provided with function signatures within <tools></tools> XML tags.
You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into
functions. Pay special attention to the properties 'types'. You should use those types as in a Python dict.
For each function call return a json object with function name and arguments within <tool_call></tool_call>
XML tags as follows:

<tool_call>
{"name": <function-name>, "arguments": <args-dict>, "id": <monotonically-increasing-id>}
</tool_call>

Here are the available tools:

<tools>
%s
</tools>
"""


class ToolAgent:
    """
    The ToolAgent class represents an agent that can interact with a language model and use tools to assist with user
    queries. It generates function calls based on user input, validates arguments, and runs the respective tools.

    Attributes:
        tools: A list of tools available to the agent.
        model: The model to be used for generating tool calls and responses.
        client: The LLM model client used to interact with the language model.
        tools_dict: A dictionary mapping tool names to their corresponding Tool objects.
    """

    def __init__(self,
                 tools: Tool | list[Tool],
                 model: str = "openai:gpt-4o-mini"):
        self.client = ai.Client()
        self.model = model
        self.tools = tools if isinstance(tools, list) else [tools]
        self.tools_dict = {tool.name: tool for tool in self.tools}

    def add_tool_signature(self):
        """
        Collects the function signatures of all available tools.

        :return: A concatenated string of all tool function signatures in JSON format.
        """
        return "".join([tool.fn_signature for tool in self.tools])

    def process_tool_calls(self, tool_calls_content: list) -> dict:
        """
        Processes each tool call, validates arguments, executes the tools, and collects results.

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
            print(Fore.GREEN + f"\nTool call dict: \n{validated_tool_call}")

            result = tool.run(**validated_tool_call["arguments"])
            print(Fore.GREEN + f"\nTool result: \n{result}")

            # Store the result using the tool call ID
            observations[validated_tool_call["id"]] = result

        return observations

    def run(self,
            user_msg: str,):
        """
        Handles the full process of interacting with the language model and executing a tool based on user input.

        :param user_msg: The user's message that prompts the tool agent to act.

        :return: The final output after executing the tool and generating a response from the model.
        """
        user_prompt = build_prompt_structure(prompt=user_msg, role="user")

        tool_chat_history = ChatHistory([
            build_prompt_structure(prompt=TOOL_SYSTEM_PROMPT % self.add_tool_signature(),
                                   role="system"),
            user_prompt
        ])
        agent_chat_history = ChatHistory([user_prompt])

        tool_call_response = completions_create(
            self.client, messages=tool_chat_history, model=self.model
        )
        tool_calls = extract_tag_content(str(tool_call_response), "tool_call")

        if tool_calls.found:
            observations = self.process_tool_calls(tool_calls.content)
            update_chat_history(
                agent_chat_history, f'f"Observation: {observations}"', "user"
            )

        return completions_create(self.client, agent_chat_history, self.model)


if __name__ == "__main__":
    def add(x: int, y: int) -> int:
        """
        A simple function to add two numbers.

        :param x: an integer
        :param y: an integer

        :return: the sum of x and y
        """
        return x + y

    from helper import tool
    add_tool = tool(add)
    tool_agent = ToolAgent(tools=[add_tool])

    user_msg = "Please add 3 and 5"
    print(tool_agent.run(user_msg))

