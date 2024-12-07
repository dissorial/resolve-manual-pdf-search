import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import fitz
import re


class PDFSearchGUI:
    def __init__(self, root, pdf_path):
        self.root = root
        self.root.title("PDF Search")

        self.root.geometry("1300x900")

        default_font = ("Segoe UI", 11)
        self.root.option_add("*Font", default_font)

        self.doc = fitz.open(pdf_path)
        self.toc = self.doc.get_toc()

        main_container = ttk.Frame(root)
        main_container.grid(row=0, column=0, sticky="nsew")
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        left_frame = ttk.Frame(main_container)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        right_frame = ttk.Frame(main_container)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        main_container.grid_columnconfigure(1, weight=3)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=1)

        search_frame = ttk.Frame(right_frame, padding="5")
        search_frame.grid(row=0, column=0, sticky="ew")
        right_frame.grid_columnconfigure(0, weight=1)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            search_frame, textvariable=self.search_var, width=60
        )
        self.search_entry.grid(row=0, column=0, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search())
        self.search_entry.focus()

        search_btn = ttk.Button(search_frame, text="Search", command=self.search)
        search_btn.grid(row=0, column=1, padx=5)

        self.case_sensitive = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            search_frame, text="Case sensitive", variable=self.case_sensitive
        ).grid(row=0, column=2, padx=5)

        nav_frame = ttk.Frame(right_frame, padding="5")
        nav_frame.grid(row=1, column=0, sticky="ew")

        ttk.Button(nav_frame, text="Previous", command=self.prev_match).grid(
            row=0, column=0, padx=5
        )
        ttk.Button(nav_frame, text="Next", command=self.next_match).grid(
            row=0, column=1, padx=5
        )

        self.results_var = tk.StringVar(value="Ready to search")
        ttk.Label(nav_frame, textvariable=self.results_var).grid(
            row=0, column=3, padx=5
        )

        self.results_list = tk.Listbox(
            left_frame,
            width=40,
            font=("Segoe UI", 11), 
            selectmode=tk.SINGLE,
            activestyle="none",
        )
        results_scrollbar = ttk.Scrollbar(
            left_frame, orient="vertical", command=self.results_list.yview
        )
        self.results_list.configure(yscrollcommand=results_scrollbar.set)

        self.results_list.grid(row=0, column=0, sticky="nsew")
        results_scrollbar.grid(row=0, column=1, sticky="ns")
        self.results_list.bind("<<ListboxSelect>>", self.on_result_select)

        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        text_frame = ttk.Frame(right_frame)
        text_frame.grid(row=2, column=0, sticky="nsew")
        right_frame.grid_rowconfigure(2, weight=1)

        self.context_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            pady=10,
            padx=10,
        )
        scrollbar = ttk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=self.context_text.yview
        )
        self.context_text.configure(yscrollcommand=scrollbar.set)

        self.context_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        self.context_text.tag_configure("match", background="yellow")
        self.context_text.tag_configure(
            "heading",
            font=("Segoe UI", 11, "bold"),
        )

        self.current_match = -1
        self.matches = []
        self.pages_with_matches = {}

    def find_headings_for_page(self, page_num):
        """Find all relevant headings for a given page number"""
        relevant_headings = []
        current_levels = [None] * 10 

        for level, title, page, *_ in self.toc:
            if page - 1 > page_num:
                break
            current_levels[level - 1] = title
            for i in range(level, len(current_levels)):
                current_levels[i] = None

        return [h for h in current_levels if h is not None]

    def on_result_select(self, event):
        """Handle selection from results list"""
        selection = self.results_list.curselection()
        if not selection:
            return

        selected_index = selection[0]

        current_line = 0
        group_index = 0

        while group_index < len(self.location_map):
            headings = self.find_headings_for_page(
                self.matches[self.location_map[group_index]][0]
            )
            group_size = len(headings) + 2

            if current_line <= selected_index < current_line + group_size:
                self.current_match = self.location_map[group_index]

                self.results_list.selection_clear(0, tk.END)
                self.results_list.selection_set(current_line)
                self.results_list.see(current_line)

                self.show_match()
                return

            current_line += group_size
            group_index += 1

    def search(self):
        search_term = self.search_var.get()
        if not search_term:
            return

        self.matches = []
        self.pages_with_matches = {}
        self.current_match = -1
        self.results_list.delete(0, tk.END)

        unique_locations = {}

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text = page.get_text()

            if not self.case_sensitive.get():
                text_to_search = text.lower()
                term_to_find = search_term.lower()
            else:
                text_to_search = text
                term_to_find = search_term

            matches_on_page = [
                m.start() for m in re.finditer(re.escape(term_to_find), text_to_search)
            ]

            if matches_on_page:
                self.pages_with_matches[page_num] = matches_on_page
                headings = self.find_headings_for_page(page_num)
                headings_tuple = tuple(headings)

                location_key = (page_num, headings_tuple)
                if location_key not in unique_locations:
                    unique_locations[location_key] = []
                unique_locations[location_key].extend(matches_on_page)

                for pos in matches_on_page:
                    self.matches.append((page_num, pos))

        self.location_map = []

        for (page_num, headings), positions in unique_locations.items():
            match_count = len(positions)
            first_match_index = next(
                i
                for i, (p, _) in enumerate(self.matches)
                if p == page_num and self.matches[i][1] == positions[0]
            )
            self.location_map.append(first_match_index)

            count_suffix = f" ({match_count} matches)" if match_count > 1 else ""
            self.results_list.insert(tk.END, f"Page {page_num + 1}{count_suffix}")

            for i, heading in enumerate(headings):
                indent = "    " * i
                self.results_list.insert(tk.END, f"{indent}▶ {heading}")
            self.results_list.insert(tk.END, "")

        total = len(self.matches)
        if total > 0:
            self.results_var.set(f"Found {total} matches")
            self.next_match()
        else:
            self.results_var.set("No matches found")
            self.context_text.delete("1.0", tk.END)

    def show_match(self):
        if not self.matches or self.current_match < 0:
            return

        page_num, pos = self.matches[self.current_match]
        page = self.doc[page_num]
        text = page.get_text()
        search_term = self.search_var.get()

        if self.case_sensitive.get():
            term_len = len(search_term)
        else:
            term_len = len(search_term)
            pos = text.lower().find(search_term.lower(), pos)

        context, match_pos = self.get_sentence_context(text, pos, term_len)

        self.context_text.delete("1.0", tk.END)

        self.context_text.insert("1.0", f"Page {page_num + 1}\n\n", "heading")

        headings = self.find_headings_for_page(page_num)
        for heading in headings:
            self.context_text.insert("end", f"▶ {heading}\n", "heading")
        self.context_text.insert("end", "\n")

        self.context_text.insert("end", context[:match_pos])
        self.context_text.insert(
            "end", context[match_pos : match_pos + term_len], "match"
        )
        self.context_text.insert("end", context[match_pos + term_len :])

        self.results_var.set(f"Match {self.current_match + 1} of {len(self.matches)}")

        current_line = 0
        for i in range(len(self.location_map)):
            if self.location_map[i] == self.current_match:
                self.results_list.selection_clear(0, tk.END)
                self.results_list.selection_set(current_line)
                self.results_list.see(current_line)
                return

            headings = self.find_headings_for_page(
                self.matches[self.location_map[i]][0]
            )
            current_line += len(headings) + 2

    def get_sentence_context(self, text, pos, search_term_len):
        text_before = text[:pos]
        text_after = text[pos + search_term_len :]

        sentence_end_before = max(
            text_before.rfind(". "), text_before.rfind("! "), text_before.rfind("? ")
        )
        if sentence_end_before == -1:
            start = max(0, pos - 200)
            if start > 0:
                while start < pos and not text[start].isspace():
                    start += 1
        else:
            start = sentence_end_before + 2

        next_period = text_after.find(". ")
        next_exclaim = text_after.find("! ")
        next_question = text_after.find("? ")
        sentence_ends = [
            e for e in [next_period, next_exclaim, next_question] if e != -1
        ]
        if sentence_ends:
            end = pos + search_term_len + min(sentence_ends) + 2
        else:
            end = min(pos + search_term_len + 200, len(text))
            while end > pos and not text[end - 1].isspace():
                end -= 1

        return text[start:end], pos - start

    def next_match(self):
        if self.matches:
            self.current_match = (self.current_match + 1) % len(self.matches)
            self.show_match()

    def prev_match(self):
        if self.matches:
            self.current_match = (self.current_match - 1) % len(self.matches)
            self.show_match()


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFSearchGUI(root, "resolve-manual.pdf")
    root.mainloop()
