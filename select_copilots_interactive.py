#!/usr/bin/env python3
"""
Robust interactive TUI for selecting copilots to install.
Handles terminal access issues and provides better error recovery.
"""

import sys
import json
import os
import select
import termios
import tty
import subprocess
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


class RobustCopilotSelector:
    def __init__(self, copilots: List[Dict]):
        self.copilots = copilots
        self.selected = set()  # Set of selected indices
        self.current_index = 0
        self.search_term = ""
        self.filtered_indices = list(range(len(copilots)))
        self.view_offset = 0  # For scrolling
        self.terminal_height = 24
        self.terminal_width = 80
        
        # Pre-compute searchable text for performance
        self.searchable_texts = []
        for copilot in copilots:
            searchable = " ".join([
                copilot.get('name', '').lower(),
                copilot.get('description', '').lower(),
                copilot.get('copilot_id', '').lower(),
                " ".join(skill.get('name', '').lower() for skill in copilot.get('skills', []))
            ])
            self.searchable_texts.append(searchable)
        
        # Group copilots by name for duplicate detection
        self.name_groups = defaultdict(list)
        for idx, copilot in enumerate(copilots):
            self.name_groups[copilot.get('name', 'Unknown')].append(idx)
    
    def get_terminal_size(self) -> Tuple[int, int]:
        """Get terminal dimensions with fallback."""
        try:
            import shutil
            cols, rows = shutil.get_terminal_size()
            self.terminal_height = rows
            self.terminal_width = cols
            return rows, cols
        except:
            return self.terminal_height, self.terminal_width
    
    def clear_screen(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end='', flush=True)
    
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
        
        return f"{name}{duplicate_indicator} • {skill_text} • {description} • ID: {id_short}"
    
    def filter_copilots(self):
        """Filter copilots based on search term."""
        if not self.search_term:
            self.filtered_indices = list(range(len(self.copilots)))
        else:
            search_lower = self.search_term.lower()
            self.filtered_indices = []
            
            # Support multiple search terms (space-separated)
            search_terms = search_lower.split()
            
            for idx, searchable_text in enumerate(self.searchable_texts):
                if all(term in searchable_text for term in search_terms):
                    self.filtered_indices.append(idx)
        
        # Reset current index if out of bounds
        if self.current_index >= len(self.filtered_indices):
            self.current_index = max(0, len(self.filtered_indices) - 1)
        
        # Reset view offset when filtering changes
        self.view_offset = 0
    
    def display(self):
        """Display the current state of the selector."""
        self.clear_screen()
        rows, cols = self.get_terminal_size()
        
        # Header
        print("🚀 Select Copilots to Install")
        print("=" * min(cols, 80))
        
        # Search display
        if self.search_term:
            print(f"🔍 Search: {self.search_term}")
        
        # Status line
        total_selected = len(self.selected)
        filtered_selected = len([i for i in self.selected if i in self.filtered_indices])
        print(f"Showing: {len(self.filtered_indices)}/{len(self.copilots)} | Selected: {filtered_selected} shown, {total_selected} total")
        print()
        
        # Controls
        print("Navigate: j/k or ↑/↓ | Select: SPACE | Search: / | Clear search: ESC")
        print("Select all: a | Deselect all: d | Confirm: ENTER | Cancel: q")
        print("-" * min(cols, 80))
        
        # Calculate display window
        header_lines = 8
        footer_lines = 2
        available_lines = rows - header_lines - footer_lines
        
        # Adjust view offset
        if self.current_index < self.view_offset:
            self.view_offset = self.current_index
        elif self.current_index >= self.view_offset + available_lines:
            self.view_offset = self.current_index - available_lines + 1
        
        # Display copilots
        if not self.filtered_indices:
            print("\n  No copilots match your search criteria.")
        else:
            for display_idx in range(available_lines):
                actual_idx = self.view_offset + display_idx
                if actual_idx >= len(self.filtered_indices):
                    break
                
                copilot_idx = self.filtered_indices[actual_idx]
                copilot = self.copilots[copilot_idx]
                
                # Selection indicator
                cursor = ">" if actual_idx == self.current_index else " "
                checkbox = "[x]" if copilot_idx in self.selected else "[ ]"
                
                # Display line
                info = self.get_display_info(copilot, copilot_idx)
                max_len = cols - 8
                if len(info) > max_len:
                    info = info[:max_len-3] + "..."
                
                print(f"{cursor} {checkbox} {info}")
        
        # Footer
        if self.view_offset + available_lines < len(self.filtered_indices):
            print(f"\n↓ {len(self.filtered_indices) - self.view_offset - available_lines} more below")
    
    def get_char(self, timeout=None):
        """Get a single character with optional timeout."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            if timeout:
                rlist, _, _ = select.select([sys.stdin], [], [], timeout)
                if rlist:
                    char = sys.stdin.read(1)
                else:
                    char = None
            else:
                char = sys.stdin.read(1)
            return char
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def handle_search_input(self):
        """Handle search mode input."""
        self.display()
        print(f"\n🔍 Search: {self.search_term}_", end='', flush=True)
        
        while True:
            char = self.get_char()
            
            if char == '\x1b':  # ESC
                self.search_term = ""
                self.filter_copilots()
                break
            elif char in ['\r', '\n']:  # ENTER
                break
            elif char in ['\x7f', '\x08']:  # Backspace
                if self.search_term:
                    self.search_term = self.search_term[:-1]
                    self.filter_copilots()
                    self.display()
                    print(f"\n🔍 Search: {self.search_term}_", end='', flush=True)
            elif char and ord(char) >= 32 and ord(char) <= 126:  # Printable
                self.search_term += char
                self.filter_copilots()
                self.display()
                print(f"\n🔍 Search: {self.search_term}_", end='', flush=True)
    
    def run(self) -> List[Dict]:
        """Run the interactive selector."""
        try:
            # Save terminal state
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            
            # If many copilots, start with search
            if len(self.copilots) > 20:
                print(f"\n📋 Found {len(self.copilots)} copilots.")
                print("Press '/' to search or any other key to browse all...")
                char = self.get_char(timeout=3)  # 3 second timeout
                if char == '/':
                    self.handle_search_input()
            
            while True:
                self.display()
                
                # Get input
                tty.setraw(sys.stdin.fileno())
                char = sys.stdin.read(1)
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                
                # Handle arrow keys
                if char == '\x1b':
                    tty.setraw(sys.stdin.fileno())
                    next_chars = sys.stdin.read(2)
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                    
                    if next_chars == '[A':  # Up arrow
                        if self.current_index > 0:
                            self.current_index -= 1
                    elif next_chars == '[B':  # Down arrow
                        if self.current_index < len(self.filtered_indices) - 1:
                            self.current_index += 1
                    else:  # ESC
                        self.search_term = ""
                        self.filter_copilots()
                
                # Handle other keys
                elif char == 'k':  # Up
                    if self.current_index > 0:
                        self.current_index -= 1
                elif char == 'j':  # Down
                    if self.current_index < len(self.filtered_indices) - 1:
                        self.current_index += 1
                elif char == ' ':  # Space - toggle selection
                    if self.filtered_indices:
                        copilot_idx = self.filtered_indices[self.current_index]
                        if copilot_idx in self.selected:
                            self.selected.remove(copilot_idx)
                        else:
                            self.selected.add(copilot_idx)
                elif char == '/':  # Search
                    self.handle_search_input()
                elif char == 'a':  # Select all visible
                    for idx in self.filtered_indices:
                        self.selected.add(idx)
                elif char == 'd':  # Deselect all visible
                    for idx in self.filtered_indices:
                        self.selected.discard(idx)
                elif char in ['\r', '\n']:  # Enter - confirm
                    break
                elif char in ['q', '\x03']:  # q or Ctrl+C - cancel
                    return []
            
            # Return selected copilots
            return [self.copilots[i] for i in sorted(self.selected)]
            
        except Exception as e:
            # On error, provide a fallback selection mechanism
            print(f"\nError in interactive mode: {e}", file=sys.stderr)
            print("Falling back to simple selection...", file=sys.stderr)
            return self.fallback_selection()
        finally:
            # Restore terminal
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except:
                pass
    
    def fallback_selection(self) -> List[Dict]:
        """Simple fallback selection when TUI fails."""
        print("\n=== Copilot Selection (Simple Mode) ===")
        print("Available copilots:")
        
        for idx, copilot in enumerate(self.copilots[:20]):  # Show first 20
            name = copilot.get('name', 'Unknown')
            skills = len(copilot.get('skills', []))
            print(f"{idx + 1}. {name} ({skills} skills)")
        
        if len(self.copilots) > 20:
            print(f"... and {len(self.copilots) - 20} more")
        
        print("\nEnter copilot numbers to install (comma-separated), or 'all' for all:")
        selection = input().strip()
        
        if selection.lower() == 'all':
            return self.copilots
        
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            return [self.copilots[i] for i in indices if 0 <= i < len(self.copilots)]
        except:
            print("Invalid selection. Selecting all copilots.")
            return self.copilots


def main():
    """Main entry point."""
    # Read copilot data
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            copilot_data = json.load(f)
    else:
        copilot_data = json.load(sys.stdin)
    
    if not copilot_data:
        print("Error: No copilots found", file=sys.stderr)
        sys.exit(1)
    
    # Check if we can use interactive mode
    if not sys.stdin.isatty():
        # Not a TTY, output all copilots
        print(json.dumps(copilot_data))
        return
    
    # Run selector
    selector = RobustCopilotSelector(copilot_data)
    selected = selector.run()
    
    if not selected:
        print("No copilots selected", file=sys.stderr)
        sys.exit(1)
    
    # Output selected copilots as JSON
    print(json.dumps(selected))


if __name__ == "__main__":
    main()