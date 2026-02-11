## 2025-02-13 - [TUI Destructive Actions]
**Learning:** Destructive actions like `delete` in Textual TUI apps can be dangerous if triggered immediately on keypress. The standard practice of modal confirmation is essential and easy to implement using `ModalScreen`.
**Action:** Always wrap `delete`, `move` (overwrite risk), and `copy` (overwrite risk) actions in a `ConfirmationScreen` modal. Use `self.push_screen(screen, callback)` for async confirmation flows.
