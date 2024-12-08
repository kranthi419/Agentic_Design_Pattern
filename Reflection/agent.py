import aisuite as ai
from dotenv import load_dotenv, find_dotenv
from colorama import Fore

from utils.completions import (completions_create, FixedFirstChatHistory, build_prompt_structure,
                               update_chat_history)
from utils.logging import fancy_step_tracker

_ = load_dotenv(find_dotenv())


BASE_GENERATION_SYSTEM_PROMPT = """
Your task is to Generate the best content possible for the user's request.
If the user provides critique, respond with a revised version of your previous attempt.
You must always output the revised content.
"""

BASE_REFLECTION_SYSTEM_PROMPT = """
You are tasked with generating critique and recommendations to the user's generated content.
If the user content has something wrong or something to be improved, output a list of recommendations
and critiques. If the user content is ok and there's nothing to change. output this: <OK>
"""


class ReflectionAgent:
    """
    A class that implements a Reflection Agent, which generates responses and reflects
    on them using the LLM to iteratively improve the interaction. The agent first generates
    responses bases on provided prompts and the critiques them in a reflection step.

    Attributes:
        model: The model name used for generating and reflecting on responses.
        client: An instance of the LLM client to interact with the language model.
    """

    def __init__(self, model: str = "openai:gpt-4o-mini"):
        self.client = ai.Client()
        self.model = model

    def _request_completion(self, history: list, verbose: int = 0, log_title: str = "COMPLETION",
                            log_color: str = "", ):
        """
        A private method to request a completion from the LLM model.

        :param history: A list of messages forming the conversation or reflection history.
        :param verbose: The verbosity level. Default is 0.

        :return: The model generated response.
        """
        output = completions_create(self.client, history, self.model)

        if verbose > 0:
            print(log_color, f"\n\n{log_title}\n\n", output)

        return output

    def generate(self, generation_history: list, verbose: int = 0):
        """
        Generates a response based on the provided generation history using the model.

        :param generation_history: A list of messages forming the conversation or generation history.
        :param verbose: The verbosity level, controlling printed output. Default is 0.

        :return: The generated response.
        """
        return self._request_completion(generation_history, verbose,
                                        log_title="GENERATION", log_color=Fore.BLUE)

    def reflect(self, reflection_history: list, verbose: int = 0):
        """
        Reflects on the generation history by generating a critique or feedback.

        :param reflection_history: A list of messages forming the reflection history, typically based on
                                   the previous generation or interation.
        :param verbose: The verbosity level, controlling printed output. Default is 0.

        :return: The critique or reflection response from the model.
        """
        return self._request_completion(reflection_history, verbose,
                                        log_title="REFLECTION", log_color=Fore.GREEN)

    def run(self, user_msg: str, generation_system_prompt: str = "",
            reflection_system_prompt: str = "", n_steps: int = 10, verbose: int = 0):
        """
        Runs the ReflectionAgent over multiple steps, alternating between generating a response and reflecting
        on it for the specified number of steps.

        :param user_msg: The user message or query that initiates the interation.
        :param generation_system_prompt: The system prompt for guiding the generation process.
        :param reflection_system_prompt: The system prompt for guiding the reflection process.
        :param n_steps: The number of generate-reflect cycles to perform. Default to 3.
        :param verbose: The verbosity level controlling printed output. Default is 0.

        :return: The final generated response after all the cycles are completed.
        """
        generation_system_prompt += BASE_GENERATION_SYSTEM_PROMPT
        reflection_system_prompt += BASE_REFLECTION_SYSTEM_PROMPT

        # Given the iterative nature of the Reflection pattern, we might exhaust the LLM context (or
        # make it really slow). That's the reason I'm limiting the chat  history to 3 messsages.
        # The 'FixedFirstChatHistory' is a very simple class, that creates a Queue that always keeps
        # fixed the first message.
        generation_history = FixedFirstChatHistory(
            [
                build_prompt_structure(prompt=generation_system_prompt, role="system"),
                build_prompt_structure(prompt=user_msg, role="user")
            ],
            total_length=3
        )

        reflection_history = FixedFirstChatHistory(
            [
                build_prompt_structure(prompt=reflection_system_prompt, role="system"),
            ],
            total_length=3
        )
        generation = None
        for step in range(n_steps):
            if verbose > 0:
                fancy_step_tracker(step, n_steps)

            # Generate the response
            generation = self.generate(generation_history, verbose)
            update_chat_history(generation_history, generation, "assistant")
            update_chat_history(reflection_history, generation, "user")

            # Reflect and critique the generation
            critique = self.reflect(reflection_history, verbose)

            if "<OK>" in critique:
                print(Fore.RED,
                      "\n\nStop Sequence found. Stopping the reflection loop ... \n\n",)
                break

            update_chat_history(generation_history, critique, "user")
            update_chat_history(reflection_history, critique, "assistant")

        return generation
