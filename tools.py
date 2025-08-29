# tools.py

import os
import docker
import io
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

# --- LLM Connection ---
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.4,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# --- Agent Prompts ---

# Prompt for initial code generation
developer_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert software developer... First, write the application code. Then, in the next turn, write the test code..."),
    ("human",
     "The user's request is: {task}. "
     "Here are the current files in the directory:\n{file_state}\n\n"
     "What is the full content of the next file you want to write?")
])

# NEW: Prompt specifically for debugging
debugging_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert software developer in a debugging session. "
     "You will be given the current state of the files and the error message from the last test run. "
     "Your goal is to fix the bug. Respond with the complete, final content of the single file you want to modify. "
     "Your response should be ONLY the code, wrapped in a single markdown code block."),
    ("human",
     "Here are the current files:\n{file_state}\n\n"
     "The tests failed with this error:\n{error}\n\n"
     "What is the full, corrected content of the file you want to change?")
])


# --- The Sandbox Tool ---
def run_code_in_sandbox(task: str) -> str:
    """
    Creates a secure Docker sandbox and runs a developer agent inside it
    to complete a given coding task, including a self-healing loop.
    """
    print(f"--- Starting Sandbox for Task: {task} ---")

    language = "python"
    if "node.js" in task.lower() or "express" in task.lower() or "javascript" in task.lower():
        language = "node"
    print(f"## Detected language: {language}")

    # FIX: Completed the Node.js setup logic
    if language == "node":
        dockerfile_content = """
        FROM node:18-slim
        WORKDIR /app
        RUN npm install express jest supertest
        COPY package.json .
        RUN npm install
        """
        app_filename = "app.js"
        test_filename = "app.test.js"
        test_command = "npm test"
        package_json_content = """
        {
          "name": "sandbox-app",
          "version": "1.0.0",
          "description": "",
          "main": "app.js",
          "scripts": {
            "test": "jest"
          },
          "dependencies": {
            "express": "^4.17.1"
          },
          "devDependencies": {
            "jest": "^27.0.0",
            "supertest": "^6.0.0"
          }
        }
        """
    else: # Python setup
        dockerfile_content = "FROM python:3.11-slim\nWORKDIR /app\nRUN pip install pytest flask"
        app_filename = "app.py"
        test_filename = "test_main.py"
        test_command = "pytest"

    client = docker.from_env()
    print("## Building sandbox image...")
    # FIX: The build process is different for Node.js vs Python
    try:
        if language == "node":
            # For Node.js, we need a build context with package.json and Dockerfile
            with open("package.json", "w") as f:
                f.write(package_json_content)
            with open("Dockerfile", "w") as f:
                f.write(dockerfile_content)
            image, _ = client.images.build(path=".", tag=f"sandbox-image-{os.urandom(4).hex()}")
            os.remove("package.json")
            os.remove("Dockerfile")
        else: # Python build process
            image, _ = client.images.build(
                fileobj=io.BytesIO(dockerfile_content.encode('utf-8')),
                tag=f"sandbox-image-{os.urandom(4).hex()}"
            )
    except docker.errors.BuildError as e:
        print(f"## Docker build failed: {e}")
        return "Error: Docker build failed."

    print("## Running sandbox container...")
    container = client.containers.run(image.id, detach=True, tty=True)

    try:
        developer_chain = developer_prompt | llm | StrOutputParser()
        debugging_chain = debugging_prompt | llm | StrOutputParser()
        file_state = "No files yet."
        
        # 1. Write the main application file
        print(f"\n--- Agent: Writing application code ({app_filename})... ---")
        app_code = developer_chain.invoke({"task": task, "file_state": file_state})
        app_code = app_code.strip().replace("```python", "").replace("```javascript", "").replace("```", "")
        container.exec_run(f"bash -c 'cat <<EOF > {app_filename}\n{app_code}\nEOF'")
        file_state = f"{app_filename}:\n{app_code}"
        print(f"Wrote {app_filename}")

        # 2. Write the test file
        print(f"\n--- Agent: Writing test code ({test_filename})... ---")
        test_code = developer_chain.invoke({"task": task, "file_state": file_state})
        test_code = test_code.strip().replace("```python", "").replace("```javascript", "").replace("```", "")
        container.exec_run(f"bash -c 'cat <<EOF > {test_filename}\n{test_code}\nEOF'")
        file_state += f"\n\n{test_filename}:\n{test_code}"
        print(f"Wrote {test_filename}")

        # 3. Run tests and start self-healing loop
        for i in range(4): # Allow up to 3 attempts to fix
            print(f"\n--- Agent: Running tests (Attempt {i+1})... ---")
            exit_code, output = container.exec_run(test_command)
            test_results = output.decode('utf-8', errors='ignore')
            print(f"Test Results:\n{test_results}")

            if "failed" not in test_results.lower() and "error" not in test_results.lower():
                print("## Tests passed! Self-healing not needed.")
                break
            
            if i == 3:
                print("## Max debugging attempts reached. Aborting.")
                break

            print("\n--- Agent: Tests failed. Entering self-healing loop... ---")
            
            # Get the fix from the debugging agent
            fix_code = debugging_chain.invoke({
                "file_state": file_state,
                "error": test_results
            })
            fix_code = fix_code.strip().replace("```python", "").replace("```javascript", "").replace("```", "")

            # Intelligent patching: decide which file to overwrite
            if "test" in fix_code.lower():
                filename_to_fix = test_filename
                print(f"## Agent is attempting to fix the test file: {filename_to_fix}")
            else:
                filename_to_fix = app_filename
                print(f"## Agent is attempting to fix the app file: {filename_to_fix}")

            container.exec_run(f"bash -c 'cat <<EOF > {filename_to_fix}\n{fix_code}\nEOF'")
            
            # Update file_state for the next loop iteration
            _, output = container.exec_run(f"cat {app_filename}")
            app_code = output.decode('utf-8', errors='ignore')
            _, output = container.exec_run(f"cat {test_filename}")
            test_code = output.decode('utf-8', errors='ignore')
            file_state = f"{app_filename}:\n{app_code}\n\n{test_filename}:\n{test_code}"

        # 4. Extract the Final Code
        print("## Extracting final code from sandbox...")
        _, output = container.exec_run("bash -c 'ls -R && for f in $(find . -type f); do echo \"---$f---\"; cat $f; done'")
        final_code = output.decode('utf-8', errors='ignore')

    finally:
        print("## Cleaning up sandbox container...")
        container.stop()
        container.remove()

    print("--- Sandbox session finished. ---")
    return final_code
