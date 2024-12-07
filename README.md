# Instructions

1. Install the requirements: `pip install -r requirements.txt`
2. Put your PDF in the same directory as this script. You must name the file `resolve-manual.pdf`, otherwise it will not work. If you want to use a different file name, then change it here in `search.py`:

```python
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFSearchGUI(root, "resolve-manual.pdf")
    root.mainloop()
```

3. Run the script: `python search.py`
