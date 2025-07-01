#!/usr/bin/env python3
"""
Interactive TUI for selecting copilots to install.
Uses built-in Python libraries for maximum compatibility.
"""

import sys
import json
import os
import tty
import termios
import re
from typing import List, Dict, Tuple


class CopilotSelector:
    def __init__(self, copilots: List[Dict]):
        self.copilots = copilots
        self.selected = set()  # Set of selected indices
        self.current_index = 0
        self.search_term = ""
        self.filtered_indices = list(range(len(copilots)))
        self.view_offset = 0  # For scrolling
        
        # Check if we can use TUI
        if os.name == 'nt':
            raise Exception("Interactive TUI is not supported on Windows. Please select copilots manually.")
        if not os.path.exists('/dev/tty'):
            raise Exception("Interactive TUI requires /dev/tty device.")
        
    def get_display_info(self, copilot: Dict) -> str:
        """Get formatted display information for a copilot."""
        name = copilot.get('name', 'Unknown')
        description = copilot.get('description', 'No description')
        skill_count = len(copilot.get('skills', []))
        copilot_id = copilot.get('copilot_id', 'Unknown ID')
        
        # Truncate description if too long
        max_desc_len = 40
        if len(description) > max_desc_len:
            description = description[:max_desc_len-3] + "..."
        
        # Format with clear separation
        skill_text = f"{skill_count} skill{'s' if skill_count != 1 else ''}"
        id_short = copilot_id.split('-')[0] if '-' in copilot_id else copilot_id[:8]
        
        return f"{name} • {skill_text} • {description} • ID: {id_short}"
    
    def filter_copilots(self):
        """Filter copilots based on search term."""
        if not self.search_term:
            self.filtered_indices = list(range(len(self.copilots)))
        else:
            pattern = re.compile(self.search_term, re.IGNORECASE)
            self.filtered_indices = []
            for i, copilot in enumerate(self.copilots):
                # Search in name, description, and copilot_id
                searchable = f"{copilot.get('name', '')} {copilot.get('description', '')} {copilot.get('copilot_id', '')}"
                if pattern.search(searchable):
                    self.filtered_indices.append(i)
        
        # Reset current index if out of bounds
        if self.current_index >= len(self.filtered_indices):
            self.current_index = max(0, len(self.filtered_indices) - 1)
            
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('clear' if os.name != 'nt' else 'cls')
        
    def get_terminal_size(self) -> Tuple[int, int]:
        """Get terminal dimensions."""
        try:
            rows, cols = os.get_terminal_size()
            return rows, cols
        except:
            return 24, 80  # Default size
            
    def display(self):
        """Display the current state of the selector."""
        self.clear_screen()
        rows, cols = self.get_terminal_size()
        
        # Header
        print("🚀 Select Copilots to Install")
        print("=" * min(cols, 80))
        print()
        print("Navigation: ↑/↓ or j/k | Select: SPACE | Search: / | Select All: a | Deselect All: n")
        print("Confirm: ENTER | Quit: q")
        print(f"Search: {self.search_term if self.search_term else '(press / to search)'}")
        print()
        print("Format: Name • Skills • Description • ID")
        print("-" * min(cols, 80))
        print()
        
        # Calculate display window
        header_lines = 9  # Updated to account for new header lines
        footer_lines = 3
        available_lines = rows - header_lines - footer_lines
        
        # Adjust view offset to keep current item visible
        if self.current_index < self.view_offset:
            self.view_offset = self.current_index
        elif self.current_index >= self.view_offset + available_lines:
            self.view_offset = self.current_index - available_lines + 1
            
        # Display copilots
        if not self.filtered_indices:
            print("No copilots match your search.")
        else:
            for display_idx in range(available_lines):
                actual_idx = self.view_offset + display_idx
                if actual_idx >= len(self.filtered_indices):
                    break
                    
                copilot_idx = self.filtered_indices[actual_idx]
                copilot = self.copilots[copilot_idx]
                
                # Selection indicator
                if actual_idx == self.current_index:
                    cursor = ">"
                else:
                    cursor = " "
                    
                # Checkbox
                if copilot_idx in self.selected:
                    checkbox = "[x]"
                else:
                    checkbox = "[ ]"
                    
                # Display line
                info = self.get_display_info(copilot)
                # Truncate if too long for terminal
                max_len = cols - 8  # Account for cursor, checkbox, and spacing
                if len(info) > max_len:
                    info = info[:max_len-3] + "..."
                    
                print(f"{cursor} {checkbox} {info}")
                
        # Footer
        print()
        print(f"Selected: {len(self.selected)} of {len(self.copilots)} copilots")
        if len(self.filtered_indices) < len(self.copilots):
            print(f"Showing: {len(self.filtered_indices)} copilots (filtered)")
            
    def get_key(self):
        """Get a single keypress."""
        # Open /dev/tty for keyboard input to avoid conflict with piped data
        with open('/dev/tty', 'r') as tty_file:
            fd = tty_file.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                key = tty_file.read(1)
                
                # Handle escape sequences for arrow keys
                if key == '\x1b':
                    key += tty_file.read(2)
                    
                return key
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
    def toggle_selection(self):
        """Toggle selection of current copilot."""
        if self.filtered_indices:
            copilot_idx = self.filtered_indices[self.current_index]
            if copilot_idx in self.selected:
                self.selected.remove(copilot_idx)
            else:
                self.selected.add(copilot_idx)
                
    def search_mode(self):
        """Enter search mode."""
        self.clear_screen()
        print("Search copilots (ESC to cancel, ENTER to confirm):")
        print(f"> {self.search_term}")
        
        # Open /dev/tty for keyboard input
        with open('/dev/tty', 'r') as tty_file:
            fd = tty_file.fileno()
            old_settings = termios.tcgetattr(fd)
            
            try:
                # Set terminal to raw mode for character-by-character input
                tty.setraw(fd)
                
                while True:
                    key = tty_file.read(1)
                    
                    if key == '\x1b':  # ESC
                        break
                    elif key == '\r' or key == '\n':  # ENTER
                        self.filter_copilots()
                        break
                    elif key == '\x7f' or key == '\x08':  # Backspace
                        if self.search_term:
                            self.search_term = self.search_term[:-1]
                            # Clear line and reprint
                            sys.stdout.write('\r\033[K')
                            sys.stdout.write(f"> {self.search_term}")
                            sys.stdout.flush()
                    elif ord(key) >= 32 and ord(key) <= 126:  # Printable characters
                        self.search_term += key
                        sys.stdout.write(key)
                        sys.stdout.flush()
                        
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
    def run(self) -> List[Dict]:
        """Run the interactive selector and return selected copilots."""
        try:
            while True:
                self.display()
                key = self.get_key()
                
                if key == '\x1b[A' or key == 'k':  # Up arrow or k
                    if self.current_index > 0:
                        self.current_index -= 1
                elif key == '\x1b[B' or key == 'j':  # Down arrow or j
                    if self.current_index < len(self.filtered_indices) - 1:
                        self.current_index += 1
                elif key == ' ':  # Space
                    self.toggle_selection()
                elif key == '/':  # Search
                    self.search_mode()
                elif key == 'a':  # Select all visible
                    for idx in self.filtered_indices:
                        self.selected.add(idx)
                elif key == 'n':  # Deselect all visible
                    for idx in self.filtered_indices:
                        self.selected.discard(idx)
                elif key == '\r' or key == '\n':  # Enter
                    break
                elif key == 'q' or key == '\x03':  # q or Ctrl+C
                    return []
                    
            # Return selected copilots
            return [self.copilots[i] for i in sorted(self.selected)]
            
        except KeyboardInterrupt:
            return []
        except Exception as e:
            print(f"\nError in TUI: {e}", file=sys.stderr)
            return []


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
        # Read from stdin (fallback)
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
        
    # Run the selector
    selector = None
    try:
        selector = CopilotSelector(copilot_data)
        selected = selector.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Falling back to manual selection...", file=sys.stderr)
        # Simple fallback: select all copilots
        selected = copilot_data
    
    # Clear screen before outputting results
    if selector:
        selector.clear_screen()
    
    if not selected:
        print("No copilots selected", file=sys.stderr)
        sys.exit(1)
        
    # Output selected copilots as JSON
    print(json.dumps(selected))
    

if __name__ == "__main__":
    main()