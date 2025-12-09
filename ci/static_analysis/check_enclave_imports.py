import ast
import os
import sys
from pathlib import Path

# Define the allowed top-level imports for the enclave package
# Host code should only import from 'signal_assistant_enclave' or its direct public modules.
ALLOWED_ENCLAVE_IMPORTS = ["signal_assistant_enclave"]

def check_file_for_forbidden_imports(file_path: Path) -> bool:
    """
    Checks a single Python file for forbidden imports from the enclave package.
    Returns True if forbidden imports are found, False otherwise.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)

    forbidden_imports_found = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                module_name = alias.name
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = f"{node.module}.{module_name}"
                    else: # Relative import
                        # Resolve relative import to absolute path
                        # This is a bit tricky with AST, simpler to check top-level relative imports
                        # For now, let's assume direct absolute imports for the enclave check
                        pass # Skip for now, focus on absolute imports from enclave

                for allowed_prefix in ALLOWED_ENCLAVE_IMPORTS:
                    # Check if the import starts with an allowed prefix, but goes deeper than allowed
                    # E.g., 'signal_assistant_enclave.privacy_core' is forbidden if only 'signal_assistant_enclave' is allowed
                    if module_name.startswith(f"{allowed_prefix}."):
                        # Split by '.' and check the second part
                        parts = module_name.split('.')
                        if len(parts) > 1 and parts[0] == allowed_prefix:
                            # Now check if the actual path points to the enclave_package
                            # This needs to be a runtime check or more sophisticated static analysis
                            # For a simple check, we assume any import starting with 'signal_assistant_enclave.'
                            # and going deeper is potentially problematic IF it's not a public API.
                            # The current rule is: strictly 'signal_assistant_enclave' (top level)
                            # or modules directly under it.
                            # This initial implementation will be strict and only allow direct imports.
                            # 'signal_assistant_enclave.app' is OK, 'signal_assistant_enclave.privacy_core.core' is NOT
                            if len(parts) > 2: # e.g., signal_assistant_enclave.privacy_core.core
                                print(f"VIOLATION: Forbidden deep import '{module_name}' found in {file_path}")
                                forbidden_imports_found = True
                                break
                    elif module_name == allowed_prefix and isinstance(node, ast.ImportFrom) and node.module is not None:
                        # Handle 'from signal_assistant_enclave import app'
                        # This is generally allowed as 'app' is a public module
                        pass
                    elif module_name.startswith("enclave_package."):
                        print(f"VIOLATION: Forbidden import '{module_name}' using 'enclave_package' prefix in {file_path}")
                        forbidden_imports_found = True
                        break


    return forbidden_imports_found

def main():
    host_code_dir = Path("src/signal_assistant")
    enclave_tests_dir = Path("enclave_package/tests") # Host tests should not directly import enclave internals

    forbidden_imports_total = False

    print(f"Checking host code in '{host_code_dir}' for forbidden enclave imports...")
    for root, _, files in os.walk(host_code_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                if check_file_for_forbidden_imports(file_path):
                    forbidden_imports_total = True

    # Also check the top-level tests directory for similar violations
    print(f"Checking host-level tests for forbidden enclave imports...")
    for root, _, files in os.walk(Path("tests")):
        for file in files:
            if file.endswith(".py"):
                # Exclude enclave_package/tests from this check, as they are part of the enclave itself
                if Path(root).is_relative_to(enclave_tests_dir):
                    continue
                file_path = Path(root) / file
                if check_file_for_forbidden_imports(file_path):
                    forbidden_imports_total = True

    if forbidden_imports_total:
        print("\nBuild Verification FAILED: Forbidden enclave imports detected.")
        sys.exit(1)
    else:
        print("\nEnclave import checks PASSED: No forbidden enclave imports found in host code or tests.")

if __name__ == "__main__":
    main()
