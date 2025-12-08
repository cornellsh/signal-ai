import argparse
import sys
from signal_assistant.main import run_host

def main():
    parser = argparse.ArgumentParser(description="Signal Assistant Host Sidecar")
    parser.add_argument("--start", action="store_true", help="Start the Host Sidecar")
    
    args = parser.parse_args()
    
    if args.start:
        run_host()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

