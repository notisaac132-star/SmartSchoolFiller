"""Tkinter desktop app: open Schoology in the "school" Chrome profile and list upcoming work."""

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from . import chrome_profile, settings as settings_store
from .schoology import SchoologyClient


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SmartSchoolFiller")
        self.geometry("820x520")
        self.settings = settings_store.load()
        self.work = []

        bar = ttk.Frame(self, padding=8)
        bar.pack(fill="x")
        ttk.Button(bar, text="Open Schoology", command=self.open_schoology).pack(side="left")
        ttk.Button(bar, text="Find my work", command=self.refresh).pack(side="left", padx=6)
        ttk.Button(bar, text="Open selected", command=self.open_selected).pack(side="left")
        ttk.Button(bar, text="Mark done / undo", command=self.toggle_done).pack(side="left", padx=6)
        ttk.Button(bar, text="Settings", command=self.open_settings).pack(side="right")

        columns = ("status", "due", "course", "title")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for column, width in zip(columns, (70, 150, 200, 380)):
            self.tree.heading(column, text=column.capitalize())
            self.tree.column(column, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=8)
        self.tree.bind("<Double-1>", lambda _event: self.open_selected())

        self.status = tk.StringVar(value="Click \"Find my work\" to load upcoming assignments.")
        ttk.Label(self, textvariable=self.status, padding=8).pack(fill="x")

        if not self.settings["consumer_key"]:
            self.after(200, self.open_settings)

    # --- Chrome -------------------------------------------------------------

    def profile_directory(self):
        name = self.settings["profile_name"]
        directory = chrome_profile.find_profile(name)
        if not directory:
            found = ", ".join(sorted(chrome_profile.list_profiles().values())) or "none"
            messagebox.showerror(
                "Profile not found",
                f'No Chrome profile named "{name}" was found.\nProfiles on this computer: {found}',
            )
        return directory

    def open_url(self, url):
        directory = self.profile_directory()
        if not directory:
            return
        try:
            chrome_profile.open_in_profile(url, directory)
        except RuntimeError as error:
            messagebox.showerror("Chrome", str(error))

    def open_schoology(self):
        self.open_url(self.settings["schoology_url"])

    # --- Assignments --------------------------------------------------------

    def refresh(self):
        if not (self.settings["consumer_key"] and self.settings["consumer_secret"]):
            self.open_settings()
            return
        self.status.set("Loading assignments from Schoology...")
        client = SchoologyClient(self.settings["consumer_key"], self.settings["consumer_secret"])

        def worker():
            try:
                work = client.upcoming_work()
            except Exception as error:  # network/auth errors are shown to the user
                self.after(0, lambda: self.status.set(f"Could not load work: {error}"))
                return
            self.after(0, lambda: self.show_work(work))

        threading.Thread(target=worker, daemon=True).start()

    def show_work(self, work):
        self.work = work
        self.tree.delete(*self.tree.get_children())
        done = set(self.settings["done"])
        for index, item in enumerate(work):
            due = item.due.strftime("%a %b %d, %I:%M %p") if item.due else "No due date"
            status = "Done" if item.id in done else "To do"
            self.tree.insert("", "end", iid=str(index), values=(status, due, item.course, item.title))
        remaining = sum(1 for item in work if item.id not in done)
        self.status.set(f"{remaining} upcoming assignment(s) to do.")

    def selected(self):
        selection = self.tree.selection()
        return self.work[int(selection[0])] if selection else None

    def open_selected(self):
        item = self.selected()
        if item:
            base = self.settings["schoology_url"].rstrip("/")
            self.open_url(item.url or f"{base}/assignment/{item.id}")

    def toggle_done(self):
        item = self.selected()
        if not item:
            return
        done = self.settings["done"]
        if item.id in done:
            done.remove(item.id)
        else:
            done.append(item.id)
        settings_store.save(self.settings)
        self.show_work(self.work)

    # --- Settings -----------------------------------------------------------

    def open_settings(self):
        window = tk.Toplevel(self)
        window.title("Settings")
        window.transient(self)
        fields = [
            ("schoology_url", "Schoology URL (e.g. https://yourschool.schoology.com)"),
            ("profile_name", "Chrome profile name"),
            ("consumer_key", "Schoology API consumer key"),
            ("consumer_secret", "Schoology API consumer secret"),
        ]
        entries = {}
        for row, (key, label) in enumerate(fields):
            ttk.Label(window, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=4)
            entry = ttk.Entry(window, width=48, show="*" if key == "consumer_secret" else "")
            entry.insert(0, self.settings[key])
            entry.grid(row=row, column=1, padx=8, pady=4)
            entries[key] = entry

        ttk.Label(
            window,
            text="Get your API key and secret at <your Schoology URL>/api while signed in.",
            foreground="gray",
        ).grid(row=len(fields), column=0, columnspan=2, padx=8, sticky="w")

        def save():
            for key, entry in entries.items():
                self.settings[key] = entry.get().strip()
            settings_store.save(self.settings)
            window.destroy()

        ttk.Button(window, text="Get API key", command=lambda: self.open_url(
            entries["schoology_url"].get().strip().rstrip("/") + "/api"
        )).grid(row=len(fields) + 1, column=0, padx=8, pady=8, sticky="w")
        ttk.Button(window, text="Save", command=save).grid(row=len(fields) + 1, column=1, padx=8, pady=8, sticky="e")


def main():
    App().mainloop()
