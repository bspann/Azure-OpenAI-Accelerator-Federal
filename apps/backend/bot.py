# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import os
import re
import asyncio
import random
import requests
import json
from concurrent.futures import ThreadPoolExecutor
from langchain.chat_models import AzureChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.memory import CosmosDBChatMessageHistory
from langchain.agents import ConversationalChatAgent, AgentExecutor, Tool
from typing import Any, Dict, List, Optional, Union
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain.schema import AgentAction, AgentFinish, LLMResult

#custom libraries that we will use later in the app
from utils import DocSearchAgent, CSVTabularAgent, SQLSearchAgent, ChatGPTTool, APISearchAgent, run_agent, reduce_openapi_spec
from prompts import WELCOME_MESSAGE, CUSTOM_CHATBOT_PREFIX, CUSTOM_CHATBOT_SUFFIX

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes

os.environ["OPENAI_API_VERSION"] = os.environ.get("AZURE_OPENAI_API_VERSION")




# Callback hanlder used for the bot service to inform the client of the thought process before the final response
class BotServiceCallbackHandler(BaseCallbackHandler):
    """Callback handler to use in Bot Builder Application"""
    
    def __init__(self, turn_context: TurnContext) -> None:
        self.tc = turn_context

    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any:
        asyncio.run(self.tc.send_activity(f"LLM Error: {error}\n"))

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> Any:
        asyncio.run(self.tc.send_activity(f"Tool: {serialized['name']}\n"))
        asyncio.run(self.tc.send_activity(Activity(type=ActivityTypes.typing)))

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        if "Action Input" in action.log:
            action = action.log.split("Action Input:")[1]
            asyncio.run(self.tc.send_activity(f"\u2611 Searching: {action} ..."))
            asyncio.run(self.tc.send_activity(Activity(type=ActivityTypes.typing)))

class MyBot(ActivityHandler):
    # See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.
    
    MODEL_DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_MODEL_NAME")
    memory = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k=10)

    async def on_message_activity(self, turn_context: TurnContext):
                    
        typing_activity = Activity(type=ActivityTypes.typing)
        await turn_context.send_activity(typing_activity)
        
        cb_handler = BotServiceCallbackHandler(turn_context)
        cb_manager = CallbackManager(handlers=[cb_handler])

        llm = AzureChatOpenAI(deployment_name=self.MODEL_DEPLOYMENT_NAME, temperature=0.5, max_tokens=1000, callback_manager=cb_manager)

        # Initialize our Tools/Experts
        indexes = ["cogsrch-index-files", "cogsrch-index-csv"]
        doc_search = DocSearchAgent(llm=llm, indexes=indexes, k=10, chunks_limit=100, similarity_k=5, callback_manager=cb_manager, return_direct=True)
        vector_only_indexes = ["cogsrch-index-books-vector"]
        book_search = DocSearchAgent(llm=llm, vector_only_indexes = vector_only_indexes,
                           k=10, similarity_k=10, reranker_th=1,
                           sas_token=os.environ['BLOB_SAS_TOKEN'],
                           callback_manager=cb_manager, return_direct=True,
                           name="@booksearch",
                           description="useful when the questions includes the term: @booksearch.\n")

        #www_search = BingSearchTool(llm=llm, k=5, callback_manager=cb_manager, return_direct=True)
        sql_search = SQLSearchAgent(llm=llm, k=10, callback_manager=cb_manager, return_direct=True)
        chatgpt_search = ChatGPTTool(llm=llm, callback_manager=cb_manager, return_direct=True)

        url = 'https://disease.sh/apidocs/swagger_v3.json'
        spec = requests.get(url).json()

        api_search = APISearchAgent(llm=llm,
                            llm_search=AzureChatOpenAI(deployment_name="gpt-35-turbo-16k", temperature=0, max_tokens=1000),
                            api_spec=str(reduce_openapi_spec(spec)), 
                            limit_to_domains=["https://disease.sh/"],
                            callback_manager=cb_manager, return_direct=True)

        tools = [sql_search, doc_search, chatgpt_search, book_search, api_search] # www_search

        # Set main Agent
        llm_a = AzureChatOpenAI(deployment_name=self.MODEL_DEPLOYMENT_NAME, temperature=0.5, max_tokens=500)
        agent = ConversationalChatAgent.from_llm_and_tools(llm=llm_a, tools=tools, system_message=CUSTOM_CHATBOT_PREFIX, human_message=CUSTOM_CHATBOT_SUFFIX)
        agent_chain = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, memory=self.memory)

        # Please note below that running a non-async function like run_agent in a separate thread won't make it truly asynchronous. It allows the function to be called without blocking the event loop, but it may still have synchronous behavior internally.
        
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(ThreadPoolExecutor(), run_agent, turn_context.activity.text, agent_chain)

        await turn_context.send_activity(answer)


    async def on_members_added_activity(self, members_added: ChannelAccount, turn_context: TurnContext):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(WELCOME_MESSAGE)
