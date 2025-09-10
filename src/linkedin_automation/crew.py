import os
import google.generativeai as genai
from dotenv import load_dotenv
from crewai import Process
from crewai.project import CrewBase, agent, task, crew
from crewai_tools import SerperDevTool
from crewai import Agent, Crew, Task, Process
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from ratelimit import limits, sleep_and_retry
import time

from tools.image_generator_tool import image_generator_tool
from tools.linkedin_poster_tool import linkedin_poster_tool

load_dotenv()
text_key = os.getenv("GEMINI_API_KEY_TEXT")
image_key = os.getenv("GEMINI_API_KEY_IMAGE")

from crewai import LLM


os.environ["GEMINI_API_KEY"] = text_key
llm = LLM(
    model="gemini/gemini-2.5-flash-lite",
    temperature=0.7,
    max_rpm=5,
    respect_context_window=True
)

# For image LLM - you'll need to switch the key when using this
def get_image_llm():
    # Temporarily set the image key
    original_key = os.environ.get("GEMINI_API_KEY")
    os.environ["GEMINI_API_KEY"] = image_key
    
    llm_image = LLM(
        model="gemini/gemini-2.5-flash-image-preview",
        max_rpm=5,
        respect_context_window=True
    )
    
    # Restore original key
    if original_key:
        os.environ["GEMINI_API_KEY"] = original_key
    
    return llm_image

llm_image = get_image_llm()

 
# Tools
search_tool = SerperDevTool()

@CrewBase
class LinkedinAutomationCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    

    @agent
    def trend_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['trend_researcher'], # type: ignore[index]
            verbose=True,
            llm=llm,
            tools=[search_tool]

        )
    
    @agent
    def topic_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['topic_researcher'], # type: ignore[index]
            verbose=True,
            llm=llm,
            tools=[search_tool]
        )
    @agent
    def summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config['summarizer'], # type: ignore[index],
            llm=llm,
            verbose=True
        )
    
    @agent
    def image_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['image_generator'], # type: ignore[index]
            verbose=True,
            tools=[image_generator_tool],
            llm=llm_image
        )

    @agent
    def linkedin_poster(self) -> Agent:
        return Agent(
            config=self.agents_config['linkedin_poster'], # type: ignore[index]
            verbose=True,
            llm=llm,
            tools=[linkedin_poster_tool]
        )
    

    @task
    def find_trends_task(self) -> Task:
        return Task(
            config=self.tasks_config['find_trends_task'] # type: ignore[index]
        )
    
    @task
    def research_topic_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_topic_task'] # type: ignore[index]
        )
    
    @task
    def summarize_post_task(self) -> Task:
        return Task(
            config=self.tasks_config['summarize_post_task'] # type: ignore[index]
        )
    
    @task
    def generate_image_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_image_task'] # type: ignore[index]
        )
    
    @task
    def post_on_linkedin_task(self) -> Task:
        return Task(
            config=self.tasks_config['post_on_linkedin_task'] # type: ignore[index]
        )
    
    @crew
    def crew(self)->Crew:
        return Crew(
        agents=self.agents,  # Automatically collected by the @agent decorator
        tasks=self.tasks,
        process=Process.sequential,
        tools={
            "serper": search_tool,
            "image_generator_tool": image_generator_tool,
            "linkedin_poster_tool": linkedin_poster_tool
        },
        llm=llm)

def create_crew():
    return LinkedinAutomationCrew().crew()
