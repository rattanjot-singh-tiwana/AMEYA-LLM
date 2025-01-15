# main.py
import asyncio
from colorama import Fore, Style
from src.graph import Workflow
from dotenv import load_dotenv
import os

# Load all env variables
load_dotenv()

# config 
config = {'recursion_limit': 100}

# Initialize workflow with email from environment
default_email = os.getenv('DEFAULT_EMAIL')
if not default_email:
    raise ValueError("DEFAULT_EMAIL environment variable must be set")

print(Fore.YELLOW + f"Using email: {default_email}" + Style.RESET_ALL)

workflow = Workflow(default_email)
app = workflow.app

initial_state = {
    "emails": [],
    "current_email": {
      "id": "",
      "threadId": "",
      "messageId": "",
      "references": "",
      "sender": "",
      "subject": "",
      "body": ""
    },
    "email_category": "",
    "generated_email": "",
    "rag_queries": [],
    "retrieved_documents": "",
    "writer_messages": [],
    "sendable": False,
    "trials": 0
}

async def main():
    try:
        print(Fore.GREEN + "Starting workflow..." + Style.RESET_ALL)
        async for output in app.astream(initial_state, config):
            for key, value in output.items():
                print(Fore.CYAN + f"Finished running: {key}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"Error in workflow: {str(e)}" + Style.RESET_ALL)
        raise e

if __name__ == "__main__":
    asyncio.run(main())