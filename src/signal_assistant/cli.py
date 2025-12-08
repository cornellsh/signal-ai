import argparse
import sys
from signal_assistant.main import run_host

def main():
    parser = argparse.ArgumentParser(description="Signal Assistant CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Host command
    host_parser = subparsers.add_parser("host", help="Start the Host Sidecar")
    
    # Simulation command
    sim_parser = subparsers.add_parser("simulate", help="Run the Assistant in local simulation mode")

    # Legacy argument support
    parser.add_argument("--start", action="store_true", help="Start the Host Sidecar (Legacy)")
    
    args = parser.parse_args()
    
    if args.command == "host" or args.start:
        run_host()
    elif args.command == "simulate":
        # Lazy import to avoid side effects or dependencies when not simulating
        from signal_assistant.simulate import main as run_simulation
        run_simulation()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()