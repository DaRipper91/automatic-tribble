## 2025-02-13 - [TUI Destructive Actions]
**Learning:** Destructive actions like `delete` in Textual TUI apps can be dangerous if triggered immediately on keypress. The standard practice of modal confirmation is essential and easy to implement using `ModalScreen`.
**Action:** Always wrap `delete`, `move` (overwrite risk), and `copy` (overwrite risk) actions in a `ConfirmationScreen` modal. Use `self.push_screen(screen, callback)` for async confirmation flows.

## 2025-05-21 - [TUI Accessibility: Modal Help]
**Learning:** In keyboard-centric TUIs (like Textual), rely on persistent modals (`ModalScreen`) for help/shortcuts instead of transient toast notifications (`self.notify`). Toasts disappear too quickly for users trying to learn new keybindings, creating a frustrating experience.
**Action:** Replace help notifications with a dedicated `HelpScreen` that users can close at their own pace.

## 2025-05-21 - [TUI Accessibility: Modal Escape Binding]
**Learning:** Textual's `ModalScreen` does not automatically bind the `Escape` key to dismiss the modal. This breaks user expectation for modal dialogs.
**Action:** Explicitly add `BINDINGS = [Binding("escape", "dismiss", "Close")]` and an `action_dismiss` method (calling `self.dismiss()`) to all `ModalScreen` implementations.

## 2025-05-22 - [Python Class Shadowing]
**Learning:** Python allows multiple class definitions with the same name in a single file, with the last one silently overwriting previous ones. This can lead to confusing bugs where tests interact with a different version of the class than expected.
**Action:** Always search for duplicate class definitions when modifying a file, especially in large UI files like `screens.py`.

## 2025-05-22 - [TUI Overwrite Confirmation Pattern]
**Learning:** To implement "Overwrite" functionality when the underlying API (like `shutil` or `pathlib`) raises `FileExistsError`, use a `try...except` block that catches the error and presents a `ConfirmationScreen`. The confirmation callback can then delete the target and retry the operation.
**Action:** Use this pattern for all file operations that might conflict, ensuring the retry logic is encapsulated within the confirmation callback.
