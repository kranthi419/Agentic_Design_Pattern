

def completions_create(client, messages: list, model: str) -> str:
    """
    Sends a request to the client's 'completions.create' method to interact with the language model.

    :param client: The LLM client
    :param messages: A list of message objects containing chat history for the model.
    :param model: The model to use for generating tool calls and responses.

    :return: The content of the model's response.
    """
    response = client.chat.completions.create(messages=messages, model=model)
    return str(response.choices[0].message.content)


def build_prompt_structure(prompt: str, role: str, tag: str = "") -> dict:
    """
    Builds a structured prompt that includes the role and content.

    :param prompt: The actual content of the prompt.
    :param role: The role of the prompt. (e.g. 'user', 'assistant').
    :param tag:

    :return: A dictionary representing the structured prompt.
    """
    if tag:
        prompt = f"<{tag}> {prompt} </{tag}>"
    return {"role": role, "content": prompt}


def update_chat_history(history: list, msg: str, role: str):
    """
    Updates the chat history by appending the latest response

    :param history: The list representing the chat history.
    :param msg: The message to append to the chat history.
    :param role: The role type (e.g. 'user', 'assistant', 'system').

    """
    history.append(build_prompt_structure(prompt=msg, role=role))


class ChatHistory(list):

    def __init__(self, messages: list | None = None, total_length: int = -1):
        """
        Initializes the queue with a fixed total length.
        :param messages: A list of initial messages.
        :param total_length: The maximum number of messages the chat history can hold.
        """
        if messages is None:
            messages = []

        super().__init__(messages)
        self.total_length = total_length

    def append(self, msg: str):
        """
        Add a message to the queue.

        :param msg: The message to add to the queue.
        """
        if len(self) == self.total_length:
            self.pop(0)
        super().append(msg)


class FixedFirstChatHistory(ChatHistory):

    def __init__(self, messages: list | None = None, total_length: int = -1):
        """
        Initializes the queue with a fixed total length.

        :param messages: A list of initial messages.
        :param total_length: The maximum number of messages the chat history can hold.
        """
        super().__init__(messages, total_length)

    def append(self, msg: str):
        """
        Add a message to the queue. The first message will always stay fixed.

        :param msg: The message to add to the queue.
        """
        if len(self) == self.total_length:
            self.pop(1)
        super().append(msg)
