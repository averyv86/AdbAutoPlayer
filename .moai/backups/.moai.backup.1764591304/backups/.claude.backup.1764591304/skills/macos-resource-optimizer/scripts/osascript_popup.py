#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
macOS Native Popup Notifications - osascript Integration

Provides native macOS dialog boxes for:
- User confirmations before tab suspension
- Success/failure notifications
- Memory recovery reports
- Interactive choice dialogs

Uses AppleScript via osascript for native macOS UI integration.

Usage:
    # Confirmation dialog
    uv run scripts/osascript_popup.py --confirm "Suspend 10 tabs?"

    # Success notification
    uv run scripts/osascript_popup.py --notify "✅ 10 tabs suspended, 500 MB freed"

    # Interactive choice
    uv run scripts/osascript_popup.py --choose "Browser" "Chrome" "Firefox" "Safari"

Author: MoAI-ADK
Version: 2.0.0 (Phase 2)
Date: 2025-12-01
"""

import argparse
import subprocess
import sys
from enum import Enum
from typing import List, Optional, Tuple


class DialogType(Enum):
    """Types of macOS dialogs."""
    CONFIRM = "confirm"  # Yes/No dialog
    NOTIFY = "notify"    # Information notification
    CHOOSE = "choose"    # Multiple choice dialog
    INPUT = "input"      # Text input dialog


class OSAScriptPopup:
    """
    macOS native popup dialogs via osascript.

    Provides clean, native macOS UI for user interactions.
    """

    def __init__(self, app_name: str = "MoAI Resource Optimizer"):
        """
        Initialize popup handler.

        Args:
            app_name: Name shown in dialog title
        """
        self.app_name = app_name

    def confirm(
        self,
        message: str,
        title: Optional[str] = None,
        yes_label: str = "확인",
        no_label: str = "취소"
    ) -> bool:
        """
        Show confirmation dialog (Yes/No).

        Args:
            message: Dialog message
            title: Dialog title (optional)
            yes_label: Label for Yes button
            no_label: Label for No button

        Returns:
            True if user clicked Yes, False if No
        """
        title = title or self.app_name

        script = f'''
        display dialog "{self._escape(message)}" ¬
            with title "{self._escape(title)}" ¬
            buttons {{"{self._escape(no_label)}", "{self._escape(yes_label)}"}} ¬
            default button "{self._escape(yes_label)}" ¬
            with icon note
        '''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=60
            )

            # osascript returns "button returned:확인" when Yes is clicked
            return yes_label in result.stdout

        except subprocess.TimeoutExpired:
            print("⚠️  Dialog timed out (60 seconds)", file=sys.stderr)
            return False
        except Exception as e:
            print(f"❌ Dialog error: {e}", file=sys.stderr)
            return False

    def notify(
        self,
        message: str,
        title: Optional[str] = None,
        subtitle: Optional[str] = None
    ) -> bool:
        """
        Show notification dialog (information only).

        Args:
            message: Main message
            title: Dialog title (optional)
            subtitle: Subtitle text (optional)

        Returns:
            True if notification was shown successfully
        """
        title = title or self.app_name

        if subtitle:
            script = f'''
            display notification "{self._escape(message)}" ¬
                with title "{self._escape(title)}" ¬
                subtitle "{self._escape(subtitle)}"
            '''
        else:
            script = f'''
            display dialog "{self._escape(message)}" ¬
                with title "{self._escape(title)}" ¬
                buttons {{"확인"}} ¬
                default button "확인" ¬
                with icon note ¬
                giving up after 10
            '''

        try:
            subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=15
            )
            return True

        except Exception as e:
            print(f"❌ Notification error: {e}", file=sys.stderr)
            return False

    def choose(
        self,
        message: str,
        choices: List[str],
        title: Optional[str] = None,
        default_choice: Optional[str] = None
    ) -> Optional[str]:
        """
        Show multiple choice dialog.

        Args:
            message: Dialog message
            choices: List of choice labels
            title: Dialog title (optional)
            default_choice: Default selected choice (optional)

        Returns:
            Selected choice label, or None if cancelled
        """
        title = title or self.app_name

        if not choices:
            return None

        # Format choices for AppleScript
        choices_list = ', '.join(f'"{self._escape(c)}"' for c in choices)

        default_clause = ""
        if default_choice and default_choice in choices:
            default_clause = f'default button "{self._escape(default_choice)}"'

        script = f'''
        choose from list {{{choices_list}}} ¬
            with title "{self._escape(title)}" ¬
            with prompt "{self._escape(message)}" ¬
            {default_clause}
        '''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0 and result.stdout.strip():
                # osascript returns the selected item
                return result.stdout.strip()
            else:
                return None

        except subprocess.TimeoutExpired:
            print("⚠️  Dialog timed out (60 seconds)", file=sys.stderr)
            return None
        except Exception as e:
            print(f"❌ Dialog error: {e}", file=sys.stderr)
            return None

    def input_text(
        self,
        message: str,
        title: Optional[str] = None,
        default_text: str = ""
    ) -> Optional[str]:
        """
        Show text input dialog.

        Args:
            message: Dialog message
            title: Dialog title (optional)
            default_text: Default input text

        Returns:
            User input text, or None if cancelled
        """
        title = title or self.app_name

        script = f'''
        display dialog "{self._escape(message)}" ¬
            with title "{self._escape(title)}" ¬
            default answer "{self._escape(default_text)}" ¬
            buttons {{"취소", "확인"}} ¬
            default button "확인"
        '''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0 and result.stdout.strip():
                # Extract text from "text returned:user input"
                for line in result.stdout.split(','):
                    if 'text returned:' in line:
                        return line.split('text returned:')[1].strip()
                return None
            else:
                return None

        except subprocess.TimeoutExpired:
            print("⚠️  Dialog timed out (60 seconds)", file=sys.stderr)
            return None
        except Exception as e:
            print(f"❌ Dialog error: {e}", file=sys.stderr)
            return None

    def progress_bar(
        self,
        message: str,
        total_steps: int,
        title: Optional[str] = None
    ) -> 'ProgressBar':
        """
        Show progress bar dialog.

        Args:
            message: Dialog message
            total_steps: Total number of steps
            title: Dialog title (optional)

        Returns:
            ProgressBar context manager
        """
        return ProgressBar(message, total_steps, title or self.app_name)

    @staticmethod
    def _escape(text: str) -> str:
        """
        Escape text for AppleScript.

        Args:
            text: Raw text

        Returns:
            Escaped text safe for AppleScript
        """
        return text.replace('\\', '\\\\').replace('"', '\\"')


class ProgressBar:
    """
    Progress bar dialog context manager.

    Usage:
        with popup.progress_bar("Processing...", total_steps=10) as progress:
            for i in range(10):
                progress.update(i + 1, f"Step {i+1}/10")
                time.sleep(1)
    """

    def __init__(self, message: str, total_steps: int, title: str):
        self.message = message
        self.total_steps = total_steps
        self.title = title
        self.current_step = 0

    def __enter__(self):
        """Start progress bar."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up progress bar."""
        pass

    def update(self, current_step: int, status: Optional[str] = None):
        """
        Update progress bar.

        Args:
            current_step: Current step number (1-indexed)
            status: Optional status message
        """
        self.current_step = current_step
        percent = int((current_step / self.total_steps) * 100)

        display_message = f"{self.message}\n\n"
        if status:
            display_message += f"{status}\n"
        display_message += f"진행률: {percent}% ({current_step}/{self.total_steps})"

        # Simple notification-based progress (macOS doesn't have native progress bars via osascript)
        try:
            subprocess.run(
                ['osascript', '-e', f'''
                display notification "{OSAScriptPopup._escape(display_message)}" ¬
                    with title "{OSAScriptPopup._escape(self.title)}"
                '''],
                capture_output=True,
                timeout=2
            )
        except Exception:
            pass


def main():
    """CLI interface for testing."""
    parser = argparse.ArgumentParser(
        description='macOS Native Popup Dialogs',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--confirm', metavar='MESSAGE',
                        help='Show confirmation dialog')
    parser.add_argument('--notify', metavar='MESSAGE',
                        help='Show notification')
    parser.add_argument('--choose', nargs='+',
                        metavar=('MESSAGE', 'CHOICE'),
                        help='Show choice dialog (first arg is message, rest are choices)')
    parser.add_argument('--input', metavar='MESSAGE',
                        help='Show text input dialog')

    args = parser.parse_args()

    popup = OSAScriptPopup()

    if args.confirm:
        result = popup.confirm(args.confirm)
        print("User confirmed" if result else "User cancelled")
        sys.exit(0 if result else 1)

    elif args.notify:
        result = popup.notify(args.notify)
        sys.exit(0 if result else 1)

    elif args.choose:
        if len(args.choose) < 2:
            print("Error: --choose requires message and at least one choice", file=sys.stderr)
            sys.exit(1)

        message = args.choose[0]
        choices = args.choose[1:]
        result = popup.choose(message, choices)

        if result:
            print(f"User selected: {result}")
            sys.exit(0)
        else:
            print("User cancelled")
            sys.exit(1)

    elif args.input:
        result = popup.input_text(args.input)
        if result is not None:
            print(result)
            sys.exit(0)
        else:
            print("User cancelled", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
