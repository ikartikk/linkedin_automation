from crew import create_crew

if __name__ == "__main__":
    crew = create_crew()
    result = crew.kickoff()
    print(result)