"""Test for multiprocessing example (refactored for pytest)."""

import ast
import math
import os
import re
import subprocess
import sys
import tempfile
import time

import pytest  # Import pytest

_BINARY_DIR = os.path.realpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)
# Assume binaries are in the same location relative to the test file
# If running from a different structure, these paths might need adjustment.
_SERVER_PATH = os.path.join(_BINARY_DIR, "grpc", "grpc_server.py")
_CLIENT_PATH = os.path.join(_BINARY_DIR, "grpc", "grpc_client.py")


# --- Helper Functions (unchanged) ---

def is_prime(n):
    """Checks if a number is prime."""
    if n < 2:
        return False
    # Optimization: Check only up to the square root
    for i in range(2, int(math.ceil(math.sqrt(n))) + 1):
        if n % i == 0:
            return False
    return True


def _get_server_address(server_stream, timeout_sec=10):
    """Reads the server stream to find the binding address."""
    start_time = time.time()
    while time.time() - start_time < timeout_sec:
        # Go back to the beginning to re-read potential new output
        server_stream.seek(0)
        # Read all lines currently available
        lines = server_stream.readlines()
        for line in lines:
            matches = re.search("Binding to '(.+)'", line)
            if matches is not None:
                return matches.group(1)  # Use group(1) for the captured group
        # Avoid busy-waiting
        time.sleep(0.1)
    raise TimeoutError(f"Could not find server address in output within {timeout_sec}s")


# --- Pytest Fixture for Server Management ---

@pytest.fixture(scope="function")  # Use "module" scope if server can be reused across tests
def running_server():
    """Starts the server, yields its address, and ensures termination."""
    # Check if server executable exists before starting
    if not os.path.exists(_SERVER_PATH):
        pytest.skip(f"Server executable not found at {_SERVER_PATH}")

    # Using 'r+' mode allows reading and writing (needed for seek/read)
    # Using text=True for automatic decoding/encoding
    with tempfile.TemporaryFile(mode="r+", encoding='utf-8') as server_stdout:
        server_process = None
        try:
            server_process = subprocess.Popen(
                (sys.executable, _SERVER_PATH),
                stdout=server_stdout,
                stderr=subprocess.PIPE,  # Capture stderr too for debugging
                text=True,
                encoding='utf-8'
            )
            # Wait for the server to bind and print the address
            server_address = _get_server_address(server_stdout)
            yield server_address  # Provide the address to the test function

        finally:
            # Ensure the server process is terminated even if errors occur
            if server_process:
                server_process.terminate()
                try:
                    # Wait a bit for graceful termination
                    stdout, stderr = server_process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if termination takes too long
                    server_process.kill()
                    stdout, stderr = server_process.communicate()
                # Optional: Check stderr for server errors during test run
                # if stderr:
                #     print(f"\nServer stderr:\n{stderr}")


# --- Test Function ---

def test_multiprocessing_example(running_server):
    """Tests the client-server interaction."""
    server_address = running_server  # Get address from the fixture

    # Check if client executable exists
    if not os.path.exists(_CLIENT_PATH):
        pytest.skip(f"Client executable not found at {_CLIENT_PATH}")

    client_process = None
    # Use a temporary file for the client's output
    with tempfile.TemporaryFile(mode="r+", encoding='utf-8') as client_stdout:
        try:
            client_process = subprocess.Popen(
                (
                    _CLIENT_PATH,
                    server_address,  # Pass the address obtained from the fixture
                ),
                stdout=client_stdout,
                stderr=subprocess.PIPE,  # Capture stderr
                text=True,
                encoding='utf-8'
            )
            # Wait for the client process to complete
            client_stdout_str, client_stderr_str = client_process.communicate(timeout=30)  # Add timeout

            # Optional: Check client return code and stderr
            assert client_process.returncode == 0, f"Client exited with code {client_process.returncode}. Stderr:\n{client_stderr_str}"
            # if client_stderr_str:
            #    print(f"\nClient stderr:\n{client_stderr_str}")

            # Process the client's output
            # Go back to the start of the temp file to read its content
            client_stdout.seek(0)
            client_output_lines = client_stdout.read().strip().splitlines()

            # Ensure there is output before trying to access the last line
            assert client_output_lines, "Client produced no output"

            # Parse the last line which should contain the results
            # Use try-except for robustness against malformed output
            try:
                results = ast.literal_eval(client_output_lines[-1])
            except (SyntaxError, ValueError) as e:
                pytest.fail(f"Failed to parse client output: {e}\nOutput:\n{client_output_lines[-1]}")

            # Perform assertions using pytest's assert
            values = tuple(result[0] for result in results)
            expected_values = tuple(range(2, 10000))

            # Using tuple() for comparison as range object isn't directly comparable
            assert values == expected_values, "Sequence of numbers processed is incorrect"

            for result in results:
                # Ensure result is a list/tuple with at least 2 elements
                assert isinstance(result, (list, tuple)) and len(result) >= 2, f"Unexpected result format: {result}"
                number, is_prime_result = result[0], result[1]
                assert isinstance(number, int), f"Expected integer, got {type(number)} in {result}"
                assert isinstance(is_prime_result, bool), f"Expected boolean, got {type(is_prime_result)} in {result}"
                # Use the helper function to verify primality
                assert is_prime(number) == is_prime_result, f"Primality check failed for {number}"

        except subprocess.TimeoutExpired:
            pytest.fail(f"Client process timed out. Address: {server_address}")
        finally:
            # Ensure client process is cleaned up if it exists (though communicate should handle this)
            if client_process and client_process.poll() is None:
                client_process.kill()
                client_process.wait()

# Note: The `if __name__ == "__main__": unittest.main()` block is removed.
# Tests are run using the pytest command-line tool, e.g., `pytest your_test_file.py`
