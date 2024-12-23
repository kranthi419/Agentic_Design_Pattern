import json
from colorama import Fore
import aisuite as ai
import math
from dotenv import load_dotenv, find_dotenv

from ToolCalling.helper import Tool, validate_arguments, tool
from utils.completions import build_prompt_structure, ChatHistory, completions_create, update_chat_history
from utils.extraction import extract_tag_content


_ = load_dotenv(find_dotenv())

BASE_SYSTEM_PROMPT = ""
REACT_SYSTEM_PROMPT = """
You operate by running a loop with the following steps: Thought, Action, Observation.
You are provided with function signatures within <tools></tools> XML tags.
You may call one or more functions to assist with the user query. Don' make assumptions about what values to plug
into functions. Pay special attention to the properties 'types'. You should use those types as in a Python dict.

For each function call return a json object with function name and arguments within <tool_call></tool_call> XML tags as follows:

<tool_call>
{"name": <function-name>,"arguments": <args-dict>, "id": <monotonically-increasing-id>}
</tool_call>

Here are the available tools / actions:

<tools>
%s
</tools>

Example session:

<question>What's the current temperature in Madrid?</question>
<thought>I need to get the current weather in Madrid</thought>
<tool_call>{"name": "get_current_weather","arguments": {"location": "Madrid", "unit": "celsius"}, "id": 0}</tool_call>

You will be called again with this:

<observation>{0: {"temperature": 25, "unit": "celsius"}}</observation>

You then output:

<response>The current temperature in Madrid is 25 degrees Celsius</response>

Additional constraints:

- If the user asks you something unrelated to any of the tools above, answer freely enclosing your answer with <response></response> tags.
"""


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
                 model: str = "openai:gpt-4o-mini",
                 system_prompt: str = BASE_SYSTEM_PROMPT, ):
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
            max_rounds: int = 10) -> str:
        """
        Execute a user interaction session, where the agent processes user input, generates responses,
        handles tool calls, and updates chat history until a final response is ready or the maximum number
        of rounds is reached.

        :param user_msg: The user's message that prompts the tool agent to act.
        :param max_rounds: Maximum number of interaction rounds the agent should perform.

        :return: The final output generated by the agent after processing user input and any tool calls.
        """
        user_prompt = build_prompt_structure(prompt=user_msg, role="user", tag="question")

        if self.tools:
            self.system_prompt += (
                    "\n" + REACT_SYSTEM_PROMPT % self.add_tool_signatures()
            )
        chat_history = ChatHistory([
            build_prompt_structure(prompt=self.system_prompt,
                                   role="system"),
            user_prompt
        ])

        if self.tools:
            for _ in range(max_rounds):
                completion = completions_create(self.client, messages=chat_history, model=self.model)
                response = extract_tag_content(str(completion), "response")
                if response.found:
                    return response.content[0]
                thought = extract_tag_content(str(completion), "thought")
                tool_calls = extract_tag_content(str(completion), "tool_call")

                update_chat_history(chat_history, completion, "assistant")
                print(Fore.MAGENTA + f"\nThought: {thought.content[0]}")

                if tool_calls.found:
                    observations = self.process_tool_calls(tool_calls.content)
                    print(Fore.BLUE + f"\nObservations: {observations}")
                    update_chat_history(chat_history, f"{observations}", "user")

        return completions_create(self.client, messages=chat_history, model=self.model)


if __name__ == "__main__":
    @tool
    def sum_two_elements(a: int, b: int) -> int:
        """
        Computes the sum of two integers.

        Args:
            a (int): The first integer to be summed.
            b (int): The second integer to be summed.

        Returns:
            int: The sum of `a` and `b`.
        """
        return a + b


    @tool
    def multiply_two_elements(a: int, b: int) -> int:
        """
        Multiplies two integers.

        Args:
            a (int): The first integer to multiply.
            b (int): The second integer to multiply.

        Returns:
            int: The product of `a` and `b`.
        """
        return a * b


    @tool
    def compute_log(x: int) -> float | str:
        """
        Computes the logarithm of an integer `x` with an optional base.

        Args:
            x (int): The integer value for which the logarithm is computed. Must be greater than 0.

        Returns:
            float: The logarithm of `x` to the specified `base`.
        """
        if x <= 0:
            return "Logarithm is undefined for values less than or equal to 0."

        return math.log(x)

    agent = ReactAgent(tools=[sum_two_elements, multiply_two_elements, compute_log])
    user_msg = "I want to calculate the sum of 1234 and 5678 and multiply the result by 5. Then, I want to take the logarithm of this result"
    response = agent.run(user_msg=user_msg)
    print(f"User Message: {user_msg}")
    print(response)

