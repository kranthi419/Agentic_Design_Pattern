from autogen_design_pattern_impl.utils import get_openai_api_key

OPENAI_API_KEY = get_openai_api_key()
llm_config = {"model": "gpt-3.5-turbo"}


from autogen import ConversableAgent


agent = ConversableAgent(name="chatbot",
                         llm_config=llm_config,
                         human_input_mode="NEVER",)

# use below method for getting direct answer generation by passing messages (note: state is not maintained here)
# reply = agent.generate_reply(messages=[{"content": "tell me a joke", "role": "user"}])
# print(reply)

# Next, try setting up 2 agents as standup comedian, which interact with each here.
kranthi = ConversableAgent(name="kranthi",
                           llm_config=llm_config,
                           human_input_mode="NEVER",
                           system_message="Your name is kranthi, you're a standup comedian.",)

jeevan = ConversableAgent(name="jeevan",
                          llm_config=llm_config,
                          human_input_mode="NEVER",
                          system_message="Your name is jeevan, you're a standup comedian."
                                         "Start the next joke from the punchline of the previous joke.")

chat_result = kranthi.initiate_chat(recipient=jeevan,
                                    message="I'm kranthi. Jeevan, lets keep the jokes rolling.",
                                    max_turns=2)
print(chat_result)

import pprint

print("chat_history:")
pprint.pprint(chat_result.chat_history)
print("cost:")
pprint.pprint(chat_result.cost)
print("summary")
pprint.pprint(chat_result.summary)


# adding custom summary generation method
chat_result = kranthi.initiate_chat(recipient=jeevan,
                                    message="I'm kranthi. Jeevan, lets keep the jokes rolling.",
                                    max_turns=2,
                                    summary_method="reflection_with_llm",
                                    summary_prompt="Summarize the conversation")
pprint.pprint(chat_result.summary)

# terminating chat with termination conditions in the prompt
kranthi = ConversableAgent(name="kranthi",
                           llm_config=llm_config,
                           human_input_mode="NEVER",
                           system_message="Your name is kranthi. You're a standup comedian."
                                          "when you're ready to end the conversation, say 'I gotta go'.",
                           is_termination_msg=lambda msg: "I gotta go" in msg["content"],)
jeevan = ConversableAgent(name="jeevan",
                          llm_config=llm_config,
                          human_input_mode="NEVER",
                          system_message="Your name is jeevan. You're a standup comedian."
                                         "when you're ready to end the conversation, say 'I gotta gp'.",
                          is_termination_msg=lambda msg: 'I gotta go' in msg["content"],)
chat_result = kranthi.initiate_chat(recipient=jeevan,
                                    message="I'm kranthi. Jeevan, lets keep the jokes rolling.")
pprint.pprint(chat_result)





