#!/usr/bin/env python3
"""
Interactive TUI for selecting copilots to install.
Optimized for handling hundreds of copilots with advanced search and filtering.
"""

import sys
import json
import os
import tty
import termios
import re
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


class CopilotSelector:
    def __init__(self, copilots: List[Dict]):
        self.copilots = copilots
        self.selected = set()  # Set of selected indices
        self.current_index = 0
        self.search_term = ""
        self.filtered_indices = list(range(len(copilots)))
        self.view_offset = 0  # For scrolling
        self.search_mode_active = False
        
        # Pre-compute searchable text for performance
        self.searchable_texts = []
        for copilot in copilots:
            searchable = " ".join([
                copilot.get('name', '').lower(),
                copilot.get('description', '').lower(),
                copilot.get('copilot_id', '').lower(),
                # Include skill names in search
                " ".join(skill.get('name', '').lower() for skill in copilot.get('skills', []))
            ])
            self.searchable_texts.append(searchable)
        
        # Group copilots by name for duplicate detection
        self.name_groups = defaultdict(list)
        for idx, copilot in enumerate(copilots):
            self.name_groups[copilot.get('name', 'Unknown')].append(idx)
        
    def get_display_info(self, copilot: Dict, copilot_idx: int) -> str:
        """Get formatted display information for a copilot."""
        name = copilot.get('name', 'Unknown')
        description = copilot.get('description', 'No description')
        skill_count = len(copilot.get('skills', []))
        copilot_id = copilot.get('copilot_id', 'Unknown ID')
        
        # Check if this copilot has duplicates
        duplicate_indicator = ""
        if len(self.name_groups[name]) > 1:
            duplicate_indicator = " ⚠️"
        
        # Truncate description if too long
        max_desc_len = 35
        if len(description) > max_desc_len:
            description = description[:max_desc_len-3] + "..."
        
        # Format with clear separation
        skill_text = f"{skill_count} skill{'s' if skill_count != 1 else ''}"
        id_short = copilot_id.split('-')[0] if '-' in copilot_id else copilot_id[:8]
        
        # Highlight search matches
        display_text = f"{name}{duplicate_indicator} • {skill_text} • {description} • ID: {id_short}"
        
        if self.search_term and self.search_mode_active:
            # Simple highlighting - uppercase matching parts
            pattern = re.compile(re.escape(self.search_term), re.IGNORECASE)
            display_text = pattern.sub(lambda m: f"\033[1;33m{m.group()}\033[0m", display_text)
        
        return display_text
    
    def filter_copilots(self):
        """Filter copilots based on search term."""
        if not self.search_term:
            self.filtered_indices = list(range(len(self.copilots)))
        else:
            # Use pre-computed searchable texts for performance
            search_lower = self.search_term.lower()
            self.filtered_indices = []
            
            # Support multiple search terms (space-separated)
            search_terms = search_lower.split()
            
            for idx, searchable_text in enumerate(self.searchable_texts):
                # All terms must match
                if all(term in searchable_text for term in search_terms):
                    self.filtered_indices.append(idx)
        
        # Reset current index if out of bounds
        if self.current_index >= len(self.filtered_indices):
            self.current_index = max(0, len(self.filtered_indices) - 1)
        
        # Reset view offset when filtering changes
        self.view_offset = 0
            
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
        
        # Status line
        total_selected = len(self.selected)
        filtered_selected = len([i for i in self.selected if i in self.filtered_indices])
        status_parts = []
        
        if self.search_term:
            status_parts.append(f"Search: '{self.search_term}'")
        status_parts.append(f"Showing: {len(self.filtered_indices)}/{len(self.copilots)}")
        status_parts.append(f"Selected: {filtered_selected} shown, {total_selected} total")
        
        print(" | ".join(status_parts))
        print()
        
        # Controls
        print("🔍 Search: / (type to filter) | Navigate: ↑/↓ or j/k | Select: SPACE")
        print("Select All Shown: a | Deselect All Shown: n | Toggle All Shown: t")
        print("Clear Search: ESC | Confirm: ENTER | Cancel: q")
        print("-" * min(cols, 80))
        
        # Calculate display window
        header_lines = 8
        footer_lines = 3
        available_lines = rows - header_lines - footer_lines
        
        # Adjust view offset to keep current item visible
        if self.current_index < self.view_offset:
            self.view_offset = self.current_index
        elif self.current_index >= self.view_offset + available_lines:
            self.view_offset = self.current_index - available_lines + 1
            
        # Display copilots
        if not self.filtered_indices:
            print("\n  No copilots match your search criteria.")
            print(f"  Try different search terms or press ESC to clear the search.")
        else:
            last_displayed_idx = -1
            for display_idx in range(available_lines):
                actual_idx = self.view_offset + display_idx
                if actual_idx >= len(self.filtered_indices):
                    break
                    
                last_displayed_idx = actual_idx
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
                info = self.get_display_info(copilot, copilot_idx)
                # Truncate if too long for terminal
                max_len = cols - 8  # Account for cursor, checkbox, and spacing
                if len(info) > max_len:
                    # Remove ANSI codes for length calculation
                    clean_info = re.sub(r'\033\[[0-9;]*m', '', info)
                    if len(clean_info) > max_len:
                        info = info[:max_len-3] + "..."
                    
                print(f"{cursor} {checkbox} {info}")
                
        # Footer with context-sensitive hints
        print()
        if self.filtered_indices and last_displayed_idx >= 0:
            if last_displayed_idx < len(self.filtered_indices) - 1:
                print(f"↓ {len(self.filtered_indices) - last_displayed_idx - 1} more below")
        
        # Quick stats
        if len(self.name_groups) < len(self.copilots):
            duplicate_count = sum(1 for group in self.name_groups.values() if len(group) > 1)
            if duplicate_count > 0:
                print(f"⚠️  {duplicate_count} copilot names have duplicates (marked with ⚠️)")
            
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
                    next_chars = tty_file.read(2)
                    if next_chars == '[A':
                        return 'UP'
                    elif next_chars == '[B':
                        return 'DOWN'
                    elif next_chars == '[5':  # Page up
                        tty_file.read(1)  # consume ~
                        return 'PGUP'
                    elif next_chars == '[6':  # Page down
                        tty_file.read(1)  # consume ~
                        return 'PGDN'
                    else:
                        return 'ESC'
                    
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
                
    def live_search_mode(self):
        """Enter live search mode where typing immediately filters."""
        self.search_mode_active = True
        
        # Open /dev/tty for keyboard input
        with open('/dev/tty', 'r') as tty_file:
            fd = tty_file.fileno()
            old_settings = termios.tcgetattr(fd)
            
            try:
                # Set terminal to raw mode for character-by-character input
                tty.setraw(fd)
                
                while True:
                    # Re-display with current search
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                    self.display()
                    # Show search cursor
                    print(f"\n🔍 Search: {self.search_term}_")
                    sys.stdout.flush()
                    tty.setraw(fd)
                    
                    key = tty_file.read(1)
                    
                    if key == '\x1b':  # ESC - clear search and exit search mode
                        self.search_term = ""
                        self.filter_copilots()
                        break
                    elif key == '\r' or key == '\n':  # ENTER - exit search mode
                        break
                    elif key == '\x7f' or key == '\x08':  # Backspace
                        if self.search_term:
                            self.search_term = self.search_term[:-1]
                            self.filter_copilots()
                    elif ord(key) >= 32 and ord(key) <= 126:  # Printable characters
                        self.search_term += key
                        self.filter_copilots()
                        
            finally:
                self.search_mode_active = False
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
    def run(self) -> List[Dict]:
        """Run the interactive selector and return selected copilots."""
        # Start with search mode if there are many copilots
        if len(self.copilots) > 20:
            print(f"\n📋 Found {len(self.copilots)} copilots. Starting in search mode...")
            print("Press any key to begin searching, or ESC to see all copilots.")
            self.get_key()
            self.live_search_mode()
        
        try:
            while True:
                self.display()
                key = self.get_key()
                
                if key == 'UP' or key == 'k':  # Up arrow or k
                    if self.current_index > 0:
                        self.current_index -= 1
                elif key == 'DOWN' or key == 'j':  # Down arrow or j
                    if self.current_index < len(self.filtered_indices) - 1:
                        self.current_index += 1
                elif key == 'PGUP':  # Page up
                    self.current_index = max(0, self.current_index - 10)
                elif key == 'PGDN':  # Page down
                    self.current_index = min(len(self.filtered_indices) - 1, self.current_index + 10)
                elif key == ' ':  # Space
                    self.toggle_selection()
                elif key == '/':  # Search
                    self.live_search_mode()
                elif key == 'a':  # Select all visible
                    for idx in self.filtered_indices:
                        self.selected.add(idx)
                elif key == 'n':  # Deselect all visible
                    for idx in self.filtered_indices:
                        self.selected.discard(idx)
                elif key == 't':  # Toggle all visible
                    for idx in self.filtered_indices:
                        if idx in self.selected:
                            self.selected.discard(idx)
                        else:
                            self.selected.add(idx)
                elif key == 'ESC':  # Clear search
                    self.search_term = ""
                    self.filter_copilots()
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
        
    # Check if we can use TUI
    if os.name == 'nt':
        print("Error: Interactive TUI is not supported on Windows.", file=sys.stderr)
        print("Selecting all copilots by default.", file=sys.stderr)
        print(json.dumps(copilot_data))
        return
        
    if not os.path.exists('/dev/tty'):
        print("Error: Interactive TUI requires /dev/tty device.", file=sys.stderr)
        print("Selecting all copilots by default.", file=sys.stderr)
        print(json.dumps(copilot_data))
        return
    
    # Run the selector
    selector = CopilotSelector(copilot_data)
    selected = selector.run()
    
    # Clear screen before outputting results
    selector.clear_screen()
    
    if not selected:
        print("No copilots selected", file=sys.stderr)
        sys.exit(1)
        
    # Output selected copilots as JSON
    print(json.dumps(selected))
    

if __name__ == "__main__":
    main()