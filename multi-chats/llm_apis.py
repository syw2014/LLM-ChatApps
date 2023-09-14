# -*- encoding: utf-8 -*-
# File: llm_apis.py
"""The apis to call third-party LLM APIs."""

from collections import OrderedDict
import os
import json
import requests
import tiktoken
import datetime
import openai
import time
import copy
import yaml


class AzureGPT(object):
    def __init__(self, GPTConfig):
        """
        @param GPTConfig: The GPConfig contains two format setting base setting include api_type, api_base, api_version, api_key, another was model parameter settings.
        The config was in the config.yml.

        """
        self.config_ = GPTConfig
        self.prompt_template = ""

        # common setting for openai
        openai.api_type = self.config_["base"]["api_type"]
        openai.api_base = self.config_["base"]["api_base"]
        openai.api_version = self.config_["base"]["api_version"]
        openai.api_key = self.config_["base"]["api_key"]
        self.engine = self.config_["base"]["engine"]

        # default setting
        self.messages = [
            {"role": "system", "content": "You are an AI assistant that helps people find information."}]

    def prompt_design(self, prompt):
        """
        Design prompt template for API call
        """
        self.prompt_template = prompt

    def get_response(self, query, param_config=None, messages=[]):
        """
        Call Azure API to get the response.
        """
        if param_config is None:
            param_config = self.config_["parameters"]
            print("No paramters input use default parameters setting!")

        if len(messages) == 0:
            messages = self.messages
            print("No messages input use default messages setting!")

        messages.append({"role": "user", "content": query})

        response = openai.ChatCompletion.create(
            engine=self.engine,
            messages=messages,
            temperature=param_config["temperature"],
            max_tokens=param_config["max_tokens"],
            top_p=param_config["top_p"],
            frequency_penalty=param_config["frequency_penalty"],
            presence_penalty=param_config["presence_penalty"],
            stop=param_config["stop"])

        print("Response: ", response)

        return response


class Minimax(object):
    def __init__(self, MiniConfig):
        """
        @param MiniConfig: The MiniConfig contains two format setting base setting include model: abab5.5-chat, another was model parameter settings.
        The config was in the config.yml.

        """
        self.config_ = MiniConfig
        self.prompt_template = ""

        # Setting API group id and secret key
        self.minimax_api_key = self.config_["base"]["api_key"]
        self.minimax_group_id = self.config_["base"]["group_id"]

        # set request url
        self.url_ = self.config_[
            "base"]["api_base"] + str(self.minimax_group_id)
        self.headers_ = {"Content-Type": "application/json",
                         "Authorization": "Bearer " + self.minimax_api_key}

        # common setting for minimax
        self.model = self.config_["base"]["model"]

        # default setting
        # self.messages = [{"sender_type":"USER","sender_name":"翠花", "text": "帮我用英文翻译下面这句话：我是谁"}]
        self.messages = []

    def create_payload(self, messages, prompt, query, param_config):
        """
        Create payload for API call.
        @param messages: history user request and bot response message
        @param prompt: the default prompt template for the current calling
        @param query: user input query
        @param param_config: parameters for LLM
        """
        payload = {
            "bot_setting": [],
            "messages": [],
            "reply_constraints": {},
            "model": self.model,
            "tokens_to_generate": 1034,
            "temperature": 0.01,
            "top_p": 0.95,
        }

        # whether to use history or not
        if len(messages) > 0:
            payload["messages"] = copy.deepcopy(messages)
        elif len(self.messages) > 0:
            payload["messages"] = copy.deepcopy(self.messages)
        else:
            if (param_config is not None) and len(param_config["parameters"]["messages"]) > 0:
                print("Use param config")
                payload["messages"] = copy.deepcopy(
                    param_config["parameters"]["messages"])

        if param_config is not None:
            # bot setting
            payload["bot_setting"] = [param_config["bot_setting"]]

            # repy constraints
            payload["reply_constraints"] = param_config["reply_constraints"]

            # set model parameters
            payload["tokens_to_generate"] = param_config["parameters"]["tokens_to_generate"]
            payload["temperature"] = param_config["parameters"]["temperature"]
            payload["top_p"] = param_config["parameters"]["top_p"]

            # current input query
            payload["messages"].append({"sender_type": param_config["message_type"]["sender_type"],
                                       "sender_name": param_config["message_type"]["sender_name"], "text": query})
        else:
            payload["messages"].append(
                {"sender_type": "USER", "sender_name": "用户", "text": query})

        return payload

    def prompt_design(self, prompt):
        """
        Design prompt template for API call
        """
        self.prompt_template = prompt

    def get_response(self, query, param_config=None, messages=[]):
        """
        Call Minimax API to get the response.
        """
        if param_config is None:
            param_config = self.config_
            print("No paramters input use default parameters setting!")

        # print("Minimax Input messages->", messages)
        # construct post data
        payload = self.create_payload(messages, "", query, param_config)
        # print("Minimax after Response1 : ", messages)
        print("Minimax POST data: ", payload)
        response = requests.post(
            self.url_, headers=self.headers_, json=payload)

        return response.json()

    def response_parse(self, response):
        """
        Parse response from Minimax API
        return: reply text, message, timestamp, useage tokens number, 
        """
        reply = response["reply"]
        print("LOG: response->", response)
        # TODO: here maybe more than one choices elemetns
        messages = response["choices"][0]["messages"][-1]

        total_tokens = response["usage"]["total_tokens"]
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return reply, messages, timestamp, total_tokens


class LLMAgent(object):
    def __init__(self, config_file):
        if not os.path.exists(config_file):
            raise FileNotFoundError("Config file not found!")
        self.config_ = yaml.safe_load(open(config_file, "r"))

        if "AzureGPT" not in self.config_:
            raise KeyError("AzureGPT configuration not found in config file!")
        self.gpt_config_ = self.config_["AzureGPT"]

        # Supported llm service list
        self.llm_services_ = ["Wenxinyiyan", "AzureGPT", "Minimax", "ChatGLM"]

        # Instance of AzureGPT
        self.azureGPT_ = AzureGPT(self.gpt_config_)

        if "Minimax" not in self.config_:
            raise KeyError("Minimax configuration not found in config file!")
        self.minimax_config_ = self.config_["Minimax"]

        # Instance of Minimax
        self.minimax_ = Minimax(self.minimax_config_)

        # chat memory
        # Here we store all the input query and it's response to the list as the memory of LLMAgent the element
        # The element be like: {"sender_type": "", "sender_name": "", "text": "query", "time": ""}
        self.messages_ = []

        # total tokens the biggest number was: 16384
        self.total_tokens = 0
        # to store the total tokens at each request
        self.token_num_list = []

        # create tools to count tokens input or output
        self.token_encoding_ = tiktoken.encoding_for_model("gpt-3.5-turbo")

    def get_response(self, query, llm_service, param_config=None, use_memory=False):
        """
        Get Response from LLM service.
        @param query: User input query
        @param llm_service: Model service which model want to use for the current request
        @param param_config: Model parameters setting like temperature,top_p,if not setting use the default
        """
        if llm_service not in self.llm_services_:
            raise KeyError(
                "{} was Unsupported LLM service!".format(llm_service))

        # choose different llm
        if llm_service == "AzureGPT":
            if use_memory:
                response = self.azureGPT_.get_response(
                    query, param_config, self.messages_)
            else:
                response = self.azureGPT_.get_response(query, param_config)
        elif llm_service == "Minimax":
            if use_memory:
                print("use memory->", self.messages_)
                response = self.minimax_.get_response(
                    query, param_config, self.messages_)
            else:
                response = self.minimax_.get_response(query, param_config)
        return response

    def response_parse(self, response):
        """
        Parse response from Minimax API
        return: reply text, message, timestamp, useage tokens number, 
        """
        return self.minimax_.response_parse(response)

    def chat(self, query, llm_service, prompt, param_config):
        """
        Interface to chat with LLM based on the input prompt, in the process store the chat history in self.messages
        @param query: user input query
        @param prompt: intput prompt template
        return: response of llm 
        """

        response = self.get_response(query, llm_service, param_config, True)

        reply, message, timestamp, useage_tokens_num = self.response_parse(
            response)

        if self.total_tokens >= 16384:
            # remove the previous messages
            # TODO: find how many messages should be deleted
            print("Remove the history chat list!")
            self.token_num_list = self.token_num_list[2:]
            self.messages_ = self.messages_[2:]

        # Store user input query
        if param_config is not None:
            print("Test1->", param_config["message_type"]["sender_type"])
            self.messages_.append({"sender_type": param_config["message_type"]["sender_type"],
                                   "sender_name": param_config["message_type"]["sender_name"],
                                   "text": query})
        else:
            self.messages_.append({"sender_type": self.minimax_.config_["message_type"]["sender_type"],
                                   "sender_name": self.minimax_.config_["message_type"]["sender_name"], "text": query})

        # store llm response
        self.messages_.append(message)

        print("History messages->", self.messages_)
        self.total_tokens += useage_tokens_num
        self.token_num_list.append(useage_tokens_num)

        return reply

    def get_messages(self):
        return copy.deepcopy(self.messages_)


if __name__ == "__main__":
    config_file = "./config.yaml"
    llm_agent = LLMAgent(config_file)

    # query = "今天的故事很美好，明天的故事未知道，昨天的故事已接触，那现在该做些什么？"
    # # res = llm_agent.get_response(query, "Minimax")
    # param_config = None
    # reply = llm_agent.chat(query, "Minimax", "", None)
    # print("User: ", query)
    # print("Bot: ", reply)
    param_config = {
        "message_type": {"sender_type": "USER", "sender_name": "小翠", "text": ""},
        "bot_setting": {"bot_name": "MM智能助理", "content": "MM智能助理是一个情感陪伴专家"},
        "reply_constraints": {"sender_type": "BOT", "sender_name": "MM智能助理"},
        "parameters": {
            "stream": False,
            "temperature": 0.01,
            "top_p": 0.95,
            "tokens_to_generate": 1024,
            "mask_sensitive_info": False,
            "messages": [],
            "sample_messages": []
        }
    }

    while True:
        query = input("User: ")
        reply = llm_agent.chat(query, "Minimax", "", param_config)
        print("User: ", query)
        print("Bot: ", reply)
        print("Test history message->", llm_agent.get_messages())
