#import tkinter as tk
from tkinter import filedialog

#root = tk.Tk()
#root.withdraw()

# path = filedialog.askopenfilename(title="Select file",
#                                   multiple=False,
#                                   filetypes=(("markdown files", "*.md"), ("all files", "*.*")))

# print(type(path))
# print('|' + path + '|')

# path = filedialog.askopenfilename(title="Select file",
#                                   multiple=True,
#                                   filetypes=(("markdown files", "*.md"), ("all files", "*.*")))
# print(type(path))
# print(path)

# D:/Data/python/projects/note_utils/test/normalizer_test.md
# ('D:/Data/python/projects/note_utils/test/normalizer_test.md',
# 'D:/Data/python/projects/note_utils/test/reorder_and_replace_test.md',
# 'D:/Data/python/projects/note_utils/test/test.md')

dirs = filedialog.askdirectory(title="Select Notes Directory")
if dirs:
    print(dirs)
else:
    print("nothing selected")
