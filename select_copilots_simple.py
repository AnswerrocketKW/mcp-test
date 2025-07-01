#!/usr/bin/env python3
"""
Simple copilot selector without TUI - for environments where TUI is not available.
"""

import sys
import json

def display_copilots(copilots):
    """Display copilots in a simple list format."""
    print("\nAvailable Copilots:", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    for i, copilot in enumerate(copilots, 1):
        name = copilot.get('name', 'Unknown')
        description = copilot.get('description', 'No description')
        skill_count = len(copilot.get('skills', []))
        copilot_id = copilot.get('copilot_id', 'Unknown ID')
        
        # Truncate description if too long
        max_desc_len = 40
        if len(description) > max_desc_len:
            description = description[:max_desc_len-3] + "..."
            
        print(f"{i}. {name}", file=sys.stderr)
        print(f"   Skills: {skill_count} | {description}", file=sys.stderr)
        print(f"   ID: {copilot_id}", file=sys.stderr)
        print(file=sys.stderr)

def get_selection(max_num):
    """Get user selection from stdin."""
    print("Enter the numbers of copilots to install (comma-separated):", file=sys.stderr)
    print("Example: 1,3,5 or 'all' to select all:", file=sys.stderr)
    print("> ", end='', file=sys.stderr)
    sys.stderr.flush()
    
    try:
        # Read from terminal
        with open('/dev/tty', 'r') as tty:
            user_input = tty.readline().strip()
    except:
        # Fallback to regular input if /dev/tty not available
        sys.stderr.flush()
        user_input = sys.stdin.readline().strip()
    
    if user_input.lower() == 'all':
        return list(range(1, max_num + 1))
    
    # Parse comma-separated numbers
    selected = []
    for num in user_input.split(','):
        try:
            n = int(num.strip())
            if 1 <= n <= max_num:
                selected.append(n)
        except ValueError:
            continue
    
    return selected

def main():
    """Main function to run the copilot selector."""
    # Read copilot data from file argument or stdin
    if len(sys.argv) > 1:
        # Read from file
        try:
            with open(sys.argv[1], 'r') as f:
                copilot_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error: Could not read JSON file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin
        try:
            copilot_data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
            sys.exit(1)
    
    if not isinstance(copilot_data, list):
        print("Error: Expected a list of copilots", file=sys.stderr)
        sys.exit(1)
        
    if not copilot_data:
        print("Error: No copilots found", file=sys.stderr)
        sys.exit(1)
    
    # Display copilots
    display_copilots(copilot_data)
    
    # Get user selection
    selected_indices = get_selection(len(copilot_data))
    
    if not selected_indices:
        print("\nNo copilots selected", file=sys.stderr)
        sys.exit(1)
    
    # Get selected copilots
    selected = [copilot_data[i-1] for i in selected_indices]
    
    print(f"\nSelected {len(selected)} copilots for installation", file=sys.stderr)
    
    # Output selected copilots as JSON
    print(json.dumps(selected))

if __name__ == "__main__":
    main()