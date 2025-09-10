import os
import time
import google.generativeai as genai
from dotenv import load_dotenv
from crewai import Process
from crewai.project import CrewBase, agent, task, crew
from crewai_tools import SerperDevTool
from crewai import Agent, Crew, Task, Process, LLM
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from tools.image_generator_tool import image_generator_tool
from tools.linkedin_poster_tool import linkedin_poster_tool

# Load environment variables
load_dotenv()
text_key = os.getenv("GEMINI_API_KEY_TEXT")
image_key = os.getenv("GEMINI_API_KEY_IMAGE")

# Setup LLMs
os.environ["GEMINI_API_KEY"] = text_key
print("gemini key-->", os.getenv("GEMINI_API_KEY"))

llm_text = LLM(
    model="gemini/gemini-2.5-flash-lite",
    temperature=0.7,
    max_rpm=5,
    respect_context_window=True
)

# Tools
search_tool = SerperDevTool()

# Content Creation Crew
@CrewBase
class ContentCreationCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents_content_creation.yaml"
    tasks_config = "config/tasks_content_creation.yaml"
    
    @agent
    def trend_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['trend_researcher'],
            verbose=True,
            llm=llm_text,
            tools=[search_tool]
        )
    
    @agent
    def topic_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['topic_researcher'],
            verbose=True,
            llm=llm_text,
            tools=[search_tool]
        )
    
    @agent
    def summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config['summarizer'],
            llm=llm_text,
            verbose=True
        )
    
    @task
    def find_trends_task(self) -> Task:
        return Task(
            config=self.tasks_config['find_trends_task']
        )
    
    @task
    def research_topic_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_topic_task']
        )
    
    @task
    def summarize_post_task(self) -> Task:
        return Task(
            config=self.tasks_config['summarize_post_task']
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            llm=llm_text
        )

# Image Generation Crew
@CrewBase
class ImageGenerationCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents_image_generation.yaml"
    tasks_config = "config/tasks_image_generation.yaml"
    
    @agent
    def image_generator(self) -> Agent:
        # Switch to image API key
        os.environ["GEMINI_API_KEY"] = image_key
        print("gemini key-->", os.getenv("GEMINI_API_KEY"))

        llm_image = LLM(
            model="gemini/gemini-2.5-flash-image-preview",
            max_rpm=5,
            respect_context_window=True
        )
        
        return Agent(
            config=self.agents_config['image_generator'],
            verbose=True,
            tools=[image_generator_tool],
            llm=llm_image
        )
    
    @task
    def generate_image_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_image_task']
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential
        )

# LinkedIn Posting Crew
@CrewBase
class LinkedInPostingCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents_linkedin_posting.yaml"
    tasks_config = "config/tasks_linkedin_posting.yaml"
    
    @agent
    def linkedin_poster(self) -> Agent:
        # Switch back to text API key
        os.environ["GEMINI_API_KEY"] = text_key
        print("gemini key-->", os.getenv("GEMINI_API_KEY"))
        return Agent(
            config=self.agents_config['linkedin_poster'],
            verbose=True,
            llm=llm_text,
            tools=[linkedin_poster_tool]
        )
    
    @task
    def post_on_linkedin_task(self) -> Task:
        return Task(
            config=self.tasks_config['post_on_linkedin_task']
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            llm=llm_text
        )

# Main execution functions
def run_content_creation():
    """Run content creation crew"""
    print("Starting content creation...")
    content_crew = ContentCreationCrew().crew()
    result = content_crew.kickoff()
    print("Content creation completed!")
    return result

def run_image_generation(content_data):
    """Run image generation crew"""
    print("Starting image generation, time.sleep implemented")
    time.sleep(70)  # Delay between crews
    image_crew = ImageGenerationCrew().crew()
    result = image_crew.kickoff(inputs={"content": content_data})
    print("Image generation completed!")
    return result

def run_linkedin_posting(content_data, image_data):
    """Run LinkedIn posting crew"""
    print("Starting LinkedIn posting...")
    time.sleep(10)  # Delay between crews
    posting_crew = LinkedInPostingCrew().crew()
    result = posting_crew.kickoff(inputs={
        "content": content_data,
        "image": image_data
    })
    print("LinkedIn posting completed!")
    return result

def main():
    """Main execution pipeline"""
    # Step 1: Create content
    content_result = run_content_creation()
    
    # Step 2: Generate image
    image_result = run_image_generation(content_result.raw)
    
    # Step 3: Post to LinkedIn
    final_result = run_linkedin_posting(content_result.raw, image_result.raw)
    
    print("Pipeline completed successfully!")
    return final_result

if __name__ == "__main__":
    result = main()