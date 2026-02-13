## 2025-02-13 - [TUI Destructive Actions]
**Learning:** Destructive actions like `delete` in Textual TUI apps can be dangerous if triggered immediately on keypress. The standard practice of modal confirmation is essential and easy to implement using `ModalScreen`.
**Action:** Always wrap `delete`, `move` (overwrite risk), and `copy` (overwrite risk) actions in a `ConfirmationScreen` modal. Use `self.push_screen(screen, callback)` for async confirmation flows.

## 2025-05-21 - [TUI Accessibility: Modal Help]
**Learning:** In keyboard-centric TUIs (like Textual), rely on persistent modals (`ModalScreen`) for help/shortcuts instead of transient toast notifications (`self.notify`). Toasts disappear too quickly for users trying to learn new keybindings, creating a frustrating experience.
**Action:** Replace help notifications with a dedicated `HelpScreen` that users can close at their own pace.

## 2025-05-21 - [TUI Accessibility: Modal Escape Binding]
**Learning:** Textual's `ModalScreen` does not automatically bind the `Escape` key to dismiss the modal. This breaks user expectation for modal dialogs.
**Action:** Explicitly add `BINDINGS = [Binding("escape", "dismiss", "Close")]` and an `action_dismiss` method (calling `self.dismiss()`) to all `ModalScreen` implementations.
