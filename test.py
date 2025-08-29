# test_sandbox.py

# Import the specific function you want to test
from tools import run_code_in_sandbox

if __name__ == "__main__":
    # Define a clear, simple coding task for the test
    coding_task = "Create a simple Flask 'Hello World' web server in a file named app.py, and then write a pytest test for it."

    print("--- Starting standalone sandbox test ---")

    # Call the function directly
    final_code = run_code_in_sandbox(coding_task)

    print("\n\n########################")
    print("## Final Code from the Sandbox Test:")
    print(final_code)
    print("########################\n")

    print("--- Standalone sandbox test finished ---")