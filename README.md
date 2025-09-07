# linkedin_automation

A modular automation framework for LinkedIn tasks using CrewAI, Gemini, and custom tools.

## Project Structure

```
linkedin_automation/
├── README.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── src/
│   └── linkedin_automation/
│       ├── config/
│       │   ├── agents.yaml
│       │   └── tasks.yaml
│       ├── crew.py
│       ├── main.py
│       └── tools/
│           ├── image_generator_tool.py
│           └── linkedin_poster_tool.py
```

## Features
- Automated LinkedIn posting and research using CrewAI agents
- Google Gemini LLM integration
- Custom tools for LinkedIn posting and image generation
- Configurable agents and tasks via YAML

## Setup

1. **Clone the repository**
2. **Create and activate a virtual environment:**
	```sh
	python3 -m venv .venv
	source .venv/bin/activate
	```
3. **Install dependencies:**
	```sh
	pip install -r requirements.txt
	```
4. **Set up environment variables:**
	- Create a `.env` file in the root directory with your API keys, e.g.:
	  ```
	  GEMINI_API_KEY=your_gemini_api_key
	  SERPER_API_KEY=your_serper_api_key
	  ```

## Configuration
- **Agents:** `src/linkedin_automation/config/agents.yaml`
- **Tasks:** `src/linkedin_automation/config/tasks.yaml`

Edit these YAML files to define your agents and tasks.

## Usage

Run the main script:
```sh
python src/linkedin_automation/main.py
```

## Main Components
- `crew.py`: Defines the CrewAI agents, tasks, and crew orchestration.
- `main.py`: Entry point to run the automation workflow.
- `tools/`: Contains custom tools for image generation and LinkedIn posting.

## Extending
- Add new agents or tasks by editing the YAML config files and updating `crew.py`.
- Add new tools in the `tools/` directory and register them in `crew.py`.

## License
MIT
