import json
from pathlib import Path
from datetime import datetime

from kivy.app import App
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.graphics import Color, RoundedRectangle


APP_NAME = "Mevira Notes"

DATA_FILE = Path.home() / "mevira_notes.json"

TODO_FILE = Path.home() / "mevira_todos.json"


CATEGORIES = [
    "Study",
    "Work",
    "Ideas",
    "Finance",
    "Personal",
    "Technology",
    "Other"
]


class PremiumCard(BoxLayout):

    def __init__(self, bg_color, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*bg_color)

            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(16)]
            )

        self.bind(
            pos=self.update_rect,
            size=self.update_rect
        )

    def update_rect(self, *_):
        self.rect.pos = self.pos
        self.rect.size = self.size


class MeviraNotes(App):

    def build(self):

        self.title = APP_NAME
        Window.clearcolor = (
            0.035, 0.045, 0.075, 1
        )

        self.dark_mode = True
        self.favorites_only = False
        self.selected_category = "All Notes"

        # Purane notes ko load karega
        self.notes = self.load_notes()

        # To-Do tasks ko alag file se load karega
        self.todos = self.load_todos()

        root = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(9)
        )

                        # =========================
        # PREMIUM HEADER
        # =========================

        header = PremiumCard(
            (0.10, 0.13, 0.23, 1),
            orientation="vertical",
            size_hint_y=None,
            height=dp(135),
            padding=[dp(8), dp(4)],
            spacing=dp(2)
        )

        # APP NAME
        header.add_widget(Label(
    text="[b]MEVIRA NOTES[/b]",
    markup=True,
    font_size="25sp",
    size_hint_y=None,
    height=dp(42),
    color=(1, 0.77, 0.12, 1),
    halign="center",
    valign="middle"
))

        # TAGLINE
        header.add_widget(Label(
    text="Your ideas. Your world.",
    font_size="13sp",
    size_hint_y=None,
    height=dp(28),
    color=(0.78, 0.83, 0.93, 1),
    halign="center",
    valign="middle"
))

        root.add_widget(header)

        # =========================
        # SEARCH
        # =========================

        self.search = TextInput(
            hint_text="Search your notes...",
            multiline=False,
            size_hint_y=None,
            height=dp(45),
            padding=[dp(12), dp(10)],
            background_color=(0.12, 0.15, 0.23, 1),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.65, 0.68, 0.76, 1),
            cursor_color=(1, 0.77, 0.12, 1)
        )

        self.search.bind(
            text=lambda *_: self.refresh_notes()
        )

        root.add_widget(self.search)

        # =========================
        # CREATE NOTE BUTTON
        # =========================

        root.add_widget(self.make_button(
            "+ Create New Note",
            self.create_note,
            (0.30, 0.23, 0.75, 1),
            height=dp(48)
        ))

        # =========================
        # TODO LIST BUTTON
        # =========================

        root.add_widget(self.make_button(
            "☑ To-Do List",
            self.open_todo_list,
            (0.05, 0.42, 0.32, 1),
            height=dp(45)
        ))

        # =========================
        # CATEGORY HEADING
        # =========================

        root.add_widget(Label(
            text="[b]CATEGORIES[/b]",
            markup=True,
            size_hint_y=None,
            height=dp(25),
            font_size="15sp",
            color=(1, 0.77, 0.12, 1),
            halign="left",
            text_size=(Window.width, None)
        ))

        # =========================
        # CATEGORY BUTTONS
        # =========================

        category_grid = GridLayout(
            cols=2,
            spacing=dp(7),
            size_hint_y=None,
            height=dp(154)
        )

        category_grid.bind(
            minimum_height=category_grid.setter("height")
        )

        category_buttons = [
            ("All Notes", (0.04, 0.43, 0.56, 1)),
            ("Study", (0.15, 0.32, 0.60, 1)),
            ("Work", (0.22, 0.35, 0.48, 1)),
            ("Ideas", (0.42, 0.28, 0.65, 1)),
            ("Finance", (0.12, 0.42, 0.34, 1)),
            ("Personal", (0.50, 0.29, 0.20, 1)),
            ("Technology", (0.12, 0.37, 0.48, 1)),
            ("Other", (0.30, 0.32, 0.40, 1))
        ]

        for category, color in category_buttons:

            category_grid.add_widget(
                self.make_button(
                    category,
                    lambda c=category: self.select_category(c),
                    color,
                    height=dp(34)
                )
            )

        root.add_widget(category_grid)

        # =========================
        # FAVORITES AND THEME
        # =========================

        tools = BoxLayout(
            size_hint_y=None,
            height=dp(40),
            spacing=dp(7)
        )

        tools.add_widget(self.make_button(
            "★ Favorites",
            self.show_favorites,
            (0.44, 0.30, 0.10, 1)
        ))

        tools.add_widget(self.make_button(
            "Theme",
            self.toggle_theme,
            (0.17, 0.20, 0.29, 1)
        ))

        tools.add_widget(self.make_button(
            "Backup",
            self.backup_notes,
            (0.17, 0.20, 0.29, 1)
        ))

        root.add_widget(tools)

                # =========================
        # NOTES LIST
        # =========================

        self.scroll = ScrollView(
            do_scroll_x=False
        )

        self.notes_layout = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            padding=[0, dp(5), 0, dp(5)]
        )

        self.notes_layout.bind(
            minimum_height=self.notes_layout.setter("height")
        )

        self.scroll.add_widget(self.notes_layout)
        root.add_widget(self.scroll)

        self.refresh_notes()

        return root

    # =========================
    # BUTTON DESIGN
    # =========================

    def make_button(
        self,
        text,
        callback,
        color=(0.17, 0.20, 0.29, 1),
        height=42
    ):

        button = Button(
            text=text,
            size_hint_y=None,
            height=dp(height),
            background_normal="",
            background_color=color,
            color=(1, 1, 1, 1),
            font_size="14sp"
        )

        button.bind(on_release=lambda *_: callback())

        return button

    # =========================
    # LOAD AND SAVE NOTES
    # =========================

    def load_notes(self):

        try:
            if DATA_FILE.exists():
                with open(DATA_FILE, "r", encoding="utf-8") as file:
                    data = json.load(file)

                    if isinstance(data, list):
                        return data

        except Exception as error:
            print("Notes load error:", error)

        return []

    def save_notes(self):

        try:
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(
                    self.notes,
                    file,
                    ensure_ascii=False,
                    indent=2
                )

        except Exception as error:
            self.message("Error", str(error))

    # =========================
    # CREATE NOTE
    # =========================

    def create_note(self):

        self.edit_note(None)

    # =========================
    # ADD / EDIT NOTE
    # =========================

    def edit_note(self, note=None):

        editing = note is not None

        form = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(10)
        )

        title_input = TextInput(
            hint_text="Note title",
            text=note.get("title", "") if editing else "",
            multiline=False,
            size_hint_y=None,
            height=dp(45)
        )

        content_input = TextInput(
            hint_text="Write your note here...",
            text=note.get("content", "") if editing else "",
            multiline=True
        )

        category_input = Spinner(
            text=note.get("category", "Other") if editing else "Other",
            values=CATEGORIES,
            size_hint_y=None,
            height=dp(42)
        )

        form.add_widget(title_input)
        form.add_widget(category_input)
        form.add_widget(content_input)

        actions = BoxLayout(
            size_hint_y=None,
            height=dp(44),
            spacing=dp(7)
        )

        popup = Popup(
            title="Edit Note" if editing else "Create Note",
            content=form,
            size_hint=(0.94, 0.85)
        )

        def save_note(*_):

            title = title_input.text.strip()
            content = content_input.text.strip()

            if not title and not content:
                self.message("Empty Note", "Please enter a title or note.")
                return

            if editing:
                note["title"] = title or "Untitled"
                note["content"] = content
                note["category"] = category_input.text
                note["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")

            else:
                self.notes.insert(0, {
                    "id": str(datetime.now().timestamp()),
                    "title": title or "Untitled",
                    "content": content,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "category": category_input.text,
                    "favorite": False
                })

            self.save_notes()
            self.refresh_notes()
            popup.dismiss()

        actions.add_widget(self.make_button(
            "Cancel",
            popup.dismiss,
            (0.35, 0.20, 0.23, 1)
        ))

        actions.add_widget(self.make_button(
            "Save Note",
            save_note,
            (0.10, 0.48, 0.28, 1)
        ))

        form.add_widget(actions)
        popup.open()

    # =========================
    # DISPLAY NOTES
    # =========================

    def refresh_notes(self):

        if not hasattr(self, "notes_layout"):
            return

        self.notes_layout.clear_widgets()

        query = self.search.text.lower().strip()

        filtered = []

        for note in self.notes:

            if self.favorites_only and not note.get("favorite", False):
                continue

            if (
                self.selected_category != "All Notes"
                and note.get("category", "Other") != self.selected_category
            ):
                continue

            searchable = (
                note.get("title", "") + " " +
                note.get("content", "") + " " +
                note.get("category", "")
            ).lower()

            if query and query not in searchable:
                continue

            filtered.append(note)

        if not filtered:
            self.notes_layout.add_widget(Label(
                text="No notes found.",
                size_hint_y=None,
                height=dp(55),
                color=(0.75, 0.78, 0.85, 1)
            ))
            return

        for note in filtered:

            card = PremiumCard(
                (0.10, 0.13, 0.21, 1),
                orientation="vertical",
                size_hint_y=None,
                height=dp(150),
                padding=dp(10),
                spacing=dp(5)
            )

            title = note.get("title", "Untitled")
            content = note.get("content", "")
            category = note.get("category", "Other")

            card.add_widget(Label(
                text=f"[b]{title}[/b]",
                markup=True,
                size_hint_y=None,
                height=dp(28),
                color=(1, 0.78, 0.18, 1),
                halign="left",
                text_size=(Window.width - dp(45), None)
            ))

            preview = content[:100]

            if len(content) > 100:
                preview += "..."

            card.add_widget(Label(
                text=preview or "(Empty note)",
                size_hint_y=None,
                height=dp(42),
                color=(0.90, 0.92, 0.97, 1),
                halign="left",
                valign="middle",
                text_size=(Window.width - dp(45), dp(42))
            ))

            card.add_widget(Label(
                text=f"{category}  •  {note.get('date', '')}",
                size_hint_y=None,
                height=dp(20),
                font_size="11sp",
                color=(0.65, 0.70, 0.80, 1),
                halign="left",
                text_size=(Window.width - dp(45), None)
            ))

            actions = BoxLayout(
                size_hint_y=None,
                height=dp(32),
                spacing=dp(5)
            )

            actions.add_widget(self.make_button(
                "Open / Edit",
                lambda n=note: self.edit_note(n),
                (0.20, 0.32, 0.60, 1),
                height=32
            ))

            actions.add_widget(self.make_button(
                "Favorite ★" if note.get("favorite", False) else "☆ Favorite",
                lambda n=note: self.toggle_favorite(n),
                (0.45, 0.30, 0.10, 1),
                height=32
            ))

            card.add_widget(actions)
            self.notes_layout.add_widget(card)
            
                    # =========================
    # SELECT CATEGORY
    # =========================

    def select_category(self, category):
        self.selected_category = category
        self.favorites_only = False
        self.refresh_notes()

    # =========================
    # SHOW FAVORITES
    # =========================

    def show_favorites(self):
        self.favorites_only = not self.favorites_only

        if self.favorites_only:
            self.selected_category = "All Notes"

        self.refresh_notes()

    # =========================
    # TOGGLE FAVORITE
    # =========================

    def toggle_favorite(self, note):
        note["favorite"] = not note.get("favorite", False)
        self.save_notes()
        self.refresh_notes()

    # =========================
    # TOGGLE THEME
    # =========================

    def toggle_theme(self):

        self.dark_mode = not self.dark_mode

        if self.dark_mode:
            Window.clearcolor = (
                0.035, 0.045, 0.075, 1
            )
        else:
            Window.clearcolor = (
                0.88, 0.90, 0.94, 1
            )

        self.message(
            "Theme Changed",
            "Dark mode enabled." if self.dark_mode
            else "Light mode enabled."
        )

    # =========================
    # BACKUP NOTES
    # =========================

    def backup_notes(self):

        backup_file = Path.home() / "mevira_notes_backup.json"

        try:
            with open(backup_file, "w", encoding="utf-8") as file:
                json.dump(
                    self.notes,
                    file,
                    ensure_ascii=False,
                    indent=2
                )

            self.message(
                "Backup Successful",
                f"Notes backup saved at:\n{backup_file}"
            )

        except Exception as error:
            self.message(
                "Backup Error",
                str(error)
            )

    # =========================
    # COPY NOTE
    # =========================

    def copy_note(self, note):

        text = (
            note.get("title", "") +
            "\n\n" +
            note.get("content", "")
        )

        Clipboard.copy(text)

        self.message(
            "Copied",
            "Note copied to clipboard."
        )

    # =========================
    # DELETE NOTE
    # =========================

    def delete_note(self, note):

        box = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(10)
        )

        box.add_widget(Label(
            text="Delete this note?",
            color=(1, 1, 1, 1)
        ))

        buttons = BoxLayout(
            size_hint_y=None,
            height=dp(44),
            spacing=dp(8)
        )

        popup = Popup(
            title="Confirm Delete",
            content=box,
            size_hint=(0.82, 0.35)
        )

        def confirm_delete():

            if note in self.notes:
                self.notes.remove(note)

            self.save_notes()
            self.refresh_notes()
            popup.dismiss()

        buttons.add_widget(self.make_button(
            "Cancel",
            popup.dismiss,
            (0.30, 0.32, 0.40, 1)
        ))

        buttons.add_widget(self.make_button(
            "Delete",
            confirm_delete,
            (0.65, 0.12, 0.18, 1)
        ))

        box.add_widget(buttons)
        popup.open()

    # =========================
    # MESSAGE POPUP
    # =========================

    def message(self, title, text):

        box = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(10)
        )

        box.add_widget(Label(
            text=str(text),
            halign="center",
            valign="middle",
            color=(1, 1, 1, 1)
        ))

        popup = Popup(
            title=title,
            content=box,
            size_hint=(0.88, 0.42)
        )

        box.add_widget(self.make_button(
            "OK",
            popup.dismiss,
            (0.20, 0.35, 0.60, 1)
        ))

        popup.open()
        
                # =========================
    # LOAD TODO TASKS
    # =========================

    def load_todos(self):

        try:
            if TODO_FILE.exists():
                with open(TODO_FILE, "r", encoding="utf-8") as file:
                    data = json.load(file)

                    if isinstance(data, list):
                        return data

        except Exception as error:
            print("To-Do load error:", error)

        return []

    # =========================
    # SAVE TODO TASKS
    # =========================

    def save_todos(self):

        try:
            with open(TODO_FILE, "w", encoding="utf-8") as file:
                json.dump(
                    self.todos,
                    file,
                    ensure_ascii=False,
                    indent=2
                )

        except Exception as error:
            self.message("Save Error", str(error))

    # =========================
    # OPEN TODO LIST
    # =========================

    def open_todo_list(self):

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        # Task input
        self.todo_input = TextInput(
            hint_text="Enter a new task...",
            multiline=False,
            size_hint_y=None,
            height=dp(45)
        )

        layout.add_widget(self.todo_input)

        # Add task button
        layout.add_widget(self.make_button(
            "+ Add Task",
            self.add_todo,
            (0.08, 0.45, 0.27, 1)
        ))

        # Task list
        self.todo_scroll = ScrollView(
            do_scroll_x=False
        )

        self.todo_layout = BoxLayout(
            orientation="vertical",
            spacing=dp(7),
            size_hint_y=None
        )

        self.todo_layout.bind(
            minimum_height=self.todo_layout.setter("height")
        )

        self.todo_scroll.add_widget(self.todo_layout)
        layout.add_widget(self.todo_scroll)

        # Close button
        layout.add_widget(self.make_button(
            "Close",
            lambda: popup.dismiss(),
            (0.35, 0.20, 0.23, 1)
        ))

        popup = Popup(
            title="Mevira To-Do List",
            content=layout,
            size_hint=(0.95, 0.88)
        )

        self.todo_popup = popup

        self.refresh_todos()
        popup.open()

    # =========================
    # ADD TODO
    # =========================

    def add_todo(self):

        task_text = self.todo_input.text.strip()

        if not task_text:
            self.message(
                "Empty Task",
                "Please enter a task first."
            )
            return

        task = {
            "id": str(datetime.now().timestamp()),
            "task": task_text,
            "done": False,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        self.todos.insert(0, task)

        self.save_todos()

        self.todo_input.text = ""

        self.refresh_todos()

    # =========================
    # SHOW TODO TASKS
    # =========================

    def refresh_todos(self):

        if not hasattr(self, "todo_layout"):
            return

        self.todo_layout.clear_widgets()

        if not self.todos:

            self.todo_layout.add_widget(Label(
                text="No tasks yet. Add your first task!",
                size_hint_y=None,
                height=dp(55),
                color=(0.75, 0.78, 0.85, 1)
            ))

            return

        for task in self.todos:

            row = BoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(65),
                spacing=dp(5),
                padding=dp(5)
            )

            checkbox = CheckBox(
                active=task.get("done", False),
                size_hint_x=None,
                width=dp(42)
            )

            checkbox.bind(
                active=lambda instance, value, t=task:
                self.toggle_todo(t, value)
            )

            row.add_widget(checkbox)

            task_label = Label(
                text=(
                    "[s]" + task.get("task", "") + "[/s]"
                    if task.get("done", False)
                    else task.get("task", "")
                ),
                markup=True,
                color=(
                    0.60, 0.85, 0.65, 1
                ) if task.get("done", False)
                else (1, 1, 1, 1),
                halign="left",
                valign="middle",
                text_size=(Window.width * 0.43, None)
            )

            row.add_widget(task_label)

            delete_button = self.make_button(
                "Delete",
                lambda t=task: self.delete_todo(t),
                (0.62, 0.13, 0.18, 1),
                height=38
            )

            delete_button.size_hint_x = None
            delete_button.width = dp(70)

            row.add_widget(delete_button)

            self.todo_layout.add_widget(row)

    # =========================
    # MARK TASK COMPLETE
    # =========================

    def toggle_todo(self, task, value):

        task["done"] = value

        self.save_todos()
        self.refresh_todos()

    # =========================
    # DELETE TODO TASK
    # =========================

    def delete_todo(self, task):

        if task in self.todos:
            self.todos.remove(task)

        self.save_todos()
        self.refresh_todos()


# =========================
# START APPLICATION
# =========================

if __name__ == "__main__":
    MeviraNotes().run()    