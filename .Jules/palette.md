## 2025-02-13 - [TUI Destructive Actions]
**Learning:** Destructive actions like `delete` in Textual TUI apps can be dangerous if triggered immediately on keypress. The standard practice of modal confirmation is essential and easy to implement using `ModalScreen`.
**Action:** Always wrap `delete` actions in a `ConfirmationScreen` modal. Plan to add similar confirmation flows for `move` and `copy` (overwrite risk). Use `self.push_screen(screen, callback)` for async confirmation flows.
