# -*- encoding: utf-8 -*-
# File: llm_app_website.py
"""A Website to use different LLM APIs like wenxinyiyan, chatglm, minimax;
Here are some useful characters:
1. You can use different LLM APIs with the select box
2. According to different LLM Models you can set different parameters
3. With different LLM Models you can design your own Prompt templates
4. The website support multi-turn dialogue with the sepcific prompt
5. All the conversation text will be store to the local database.
6. Future the APP will support document QA with langchain or other tools
7. Future the APP will support conversation with search engine for the time-related query."""

# set page infos
from llm_apis import *
import streamlit as st
st.set_page_config(
    page_title="LLM App",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "Get Help": "https://ibb.co/G5y1H0j"},
)

# set page title
st.title(" :blue[Challis: CHAt with LLm Service]")

# from llm_apis import *
# define llm service and model selection
llm_service = st.selectbox(
    "模型服务商",  ("Wenxinyiyan", "Minimax", "ChatGLM", "AzureGPT"))
st.write("当前模型: ", llm_service)

model_name = ""

if llm_service == "Wenxinyiyan":
    model_name = st.selectbox("Model", ("ERNIE-Bot", "ERNIE-Bot-Turbo"))
elif llm_service == "Minimax":
    model_name = st.selectbox("Model", ("adab5.5-chat",))
elif llm_service == "ChatGLM":
    model_name = st.selectbox(
        "Model", ("chatglm_pro", "chatglm_std", "chatglm_lite"))
elif llm_service == "AzureGPT":
    model_name = st.selectbox("Model", ("gpt-35-turbo", "agpt-35-turbo-16k"))

# define prompt input textbox
st.caption("**Prompt模板设计**")
input_prompt = st.text_area(label="prompt", height=100,
                            placeholder="输入Prompt模板")
prompt_button = st.button("确认", key="predict")


# define placehold for llm
temperature = None
top_k = None
penalty_score = None
stream = False
tokens_to_generate = 256
max_tokens = 10
presence_penalty = None
frequency_penalty = None


# set parameters in sidebar with different model api
st.sidebar.header("Parameters for LLM")
if llm_service == "Wenxinyiyan":
    # st.sidebar.write("Parameters")
    temperature = st.sidebar.slider(
        'temperature', min_value=0.0, max_value=1.0, value=0.8)
    top_p = st.sidebar.slider('top_p', min_value=0.0, max_value=1.0, value=0.8)
    penalty_score = st.sidebar.slider(
        'penalty_score', min_value=1.0, max_value=2.0, value=1.0)
    stream = st.sidebar.checkbox('stream', value=False)

elif llm_service == "AzureGPT":
    temperature = st.sidebar.slider(
        'temperature', min_value=0.0, max_value=2.0, value=1.0)
    top_p = st.sidebar.slider('top_p', min_value=0.0, max_value=1.0, value=1.0)
    presence_penalty = st.sidebar.slider(
        'presence_penalty', min_value=-2.0, max_value=2.0, value=0.0)
    frequency_penalty = st.sidebar.slider(
        'frequency_penalty', min_value=-2.0, max_value=2.0, value=0.0)
    max_tokens = st.sidebar.slider(
        'max_tokens', min_value=16, max_value=512, value=16)
    stream = st.sidebar.checkbox('stream', value=False)
elif llm_service == "Minimax":
    temperature = st.sidebar.slider(
        'temperature', min_value=0.0, max_value=1.0, value=0.9)
    top_p = st.sidebar.slider('top_p', min_value=0.0,
                              max_value=1.0, value=0.95)
    stream = st.sidebar.checkbox('stream', value=False)
    tokens_to_generate = st.sidebar.slider(
        'tokens_to_generate', min_value=1, max_value=16383, value=1024)
elif llm_service == "ChatGLM":
    temperature = st.sidebar.slider(
        'temperature', min_value=0.0, max_value=1.0, value=0.95)
    top_p = st.sidebar.slider('top_p', min_value=0.0, max_value=1.0, value=0.7)


# define LLMAgent instance
config_file = "./config.yaml"
llm_agent = LLMAgent(config_file)


if "history" not in st.session_state:
    st.session_state.history = []

if "past_key_values" not in st.session_state:
    st.session_state.past_key_values = None


# with st.chat_message(name="user", avatar="user"):
#     input_placeholder = st.empty()

# with st.chat_message(name="assistant", avatar="assistant"):
#     message_placeholder = st.empty()

# define user input textbox
# st.caption("**聊天窗口**")
# input_query = st.text_area(label="query", height=100,
#                            placeholder="我在，请说")
# query_button = st.button("发送", key="predict2")


# define llm calling agent
def call_llm(query, llm_service, prompt, param_config):
    if llm_service == "Minimax":
        # construct history messages
        print("Hist--> ", llm_agent.get_messages())
        param_config = {
            "message_type": {"sender_type": "USER", "sender_name": "小翠", "text": ""},
            "bot_setting": {"bot_name": "MM智能助理", "content": input_prompt},
            "reply_constraints": {"sender_type": "BOT", "sender_name": "MM智能助理"},
            "parameters": {
                "stream": False,
                "temperature": 0.01,
                "top_p": 0.95,
                "tokens_to_generate": 1024,
                "mask_sensitive_info": False,
                "messages": st.session_state.history,
                "sample_messages": []
            }
        }

        # add input query
        # query = param_config["message_type"]
        # query["text"] = input_query
        # param_config["parameters"]["messages"].append(query)

        # call the api
        reply = llm_agent.chat(query, "Minimax", "", param_config)

        st.session_state.history += llm_agent.get_messages()
        print("TEEE->", st.session_state.history)

    else:
        reply = "llm service was not support!"
        print("llm service was not support!")

    return reply


# if query_button:
#     input_placeholder.markdown(input_query)
#     reply = call_llm(input_query, llm_service, "", None)
#     message_placeholder.markdown(reply)

# another way to create chatbot block
if input_query := st.chat_input("我在，请说"):
    with st.chat_message(name="user", avatar="user"):
        st.markdown(input_query)

    # response
    with st.chat_message(name="assistant", avatar="assistant"):
        message_placeholder = st.empty()
        # get response
        reply = call_llm(input_query, llm_service, "", None)
        message_placeholder.markdown(reply)

# show history conversation messages
if len(st.session_state.history) > 0:
    for chat in st.session_state.history:
        if chat["sender_type"] == "USER":
            with st.chat_message(name="user", avatar="user"):
                st.markdown(chat["text"])
        elif chat["sender_type"] == "BOT":
            with st.chat_message(name="assistant", avatar="assistant"):
                st.markdown(chat["text"])
