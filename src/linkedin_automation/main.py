# from crew import create_crew

# if __name__ == "__main__":
#     crew = create_crew()
#     result = crew.kickoff()
#     print(result)

from tools.linkedin_poster_tool import linkedin_poster_tool

if __name__ == "__main__":
    sample_content = "This is a test post from the LinkedIn automation bot."
    sample_image = None  # Or provide a path/URL if your tool supports images
    result = linkedin_poster_tool.run({"text": sample_content})
    print("LinkedIn Poster Tool Result:", result)
