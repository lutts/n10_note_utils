Cells can vary in width and do not need to be perfectly aligned within columns. There must be at least three hyphens in each column of the header row.

| Command | Description |
| --- | --- |
| git status | * List all new{nl}* modified files |
| git diff | To create a task list, preface list items with a hyphen and space followed by [ ]. To mark a task as complete, use [x].{nl}{nl}* [x] #739{nl}* [ ] https://github.com/octo-org/octo-repo/issues/740{nl}* [ ] Add delight to the experience when all tasks are complete :tada:{nl}    {nl}If a task list item description begins with a parenthesis, you'll need to escape it with \: |
    
You can align text to the left, right, or center of a column by including colons : to the left, right, or on both sides of the hyphens within the header row.

| Left-aligned | Center-aligned | Right-aligned |
| :---         |     :---:      |          ---: |
| git status   | git status     | git status    |
| git diff     | git diff       | git diff      |
    
To include a pipe | as content within your cell, use a \ before the pipe:

| Name     | Character |
| ---      | ---       |
| Backtick | `         |
| Pipe     | \|        |

command-line usage

To create a task list, preface list items with a hyphen and space followed by [ ]. To mark a task as complete, use [x].

* [x] #739
* [ ] https://github.com/octo-org/octo-repo/issues/740
* [ ] Add delight to the experience when all tasks are complete :tada:
    
If a task list item description begins with a parenthesis, you'll need to escape it with \:

* [ ] \(Optional) Open a followup issue

Parse ~~strikethrough~~ formatting

这**是(is)**一个苹果。

这**是**(**is**)一个苹果。