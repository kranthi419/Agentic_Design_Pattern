import aisuite as ai

from colorama import Fore

from utils.completions import completions_create


class ReflectionAgent:
    """
    A class that implements a Reflection Agent, which generates responses and reflects
    on them using the LLM to iteratively improve the interaction. The agent first generates
    responses bases on provided prompts and the critiques them in a reflection step.

    Attributes:
        model: The model name used for generating and reflecting on responses.
        client: An instance of the LLM client to interact with the language model.
    """

    def __init__(self, model: str = "gpt4o-mini"):
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