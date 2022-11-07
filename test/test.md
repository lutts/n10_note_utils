---
"lang": "en",
"title": "Euler's Identity",
"subtitle": "How to combine 5 important math constants to a short formula",
"authors": ["Max Muster<sup>1</sup>", "Lisa Master<sup>2</sup>"],
"adresses": ["<sup>1</sup>Hochschule Gartenstadt","<sup>2</sup>Universität Übersee"],
"date": "May 2021",
"description": "mdmath LaTeX demo site",
"tags": ["markdown+math","VSCode","static page","publication","LaTeX","math"]
---

# 标题

### 测试表格及表格内的多行支持

| Command | Description |
| --- | --- |
| git status | List all new or modified files |
| git diff | To create a task list, preface list items with a hyphen and space followed by [ ]. To mark a task as complete, use [x].{nl}{nl}* [x] #739{nl}* [ ] [octo-org](https://github.com/octo-org/octo-repo/issues/740){nl}* [ ] Add delight to the experience when all tasks are complete : tada:{nl} {nl}If a task list item description begins with a parenthesis, you'll need to escape it with \: |

You can align text to the left, right, or center of a column by including colons : to the left, right, or on both sides of the hyphens within the header row.

| Left-aligned | Center-aligned | Right-aligned |
| :--- | :---: | ---: |
| git status | git status | git status |
| git diff | git diff | git diff |

To include a pipe | as content within your cell, use a \ before the pipe:

| Name | Character |
| --- | --- |
| Backtick | ` |
| Pipe | \| |

command-line usage

## 测试task list

To create a task list, preface list items with a hyphen and space followed by [ ]. To mark a task as complete, use [x].

* [x] #739
* [ ] https://github. com/octo-org/octo-repo/issues/740
* [ ] Add delight to the experience when all tasks are complete : tada:

If a task list item description begins with a parenthesis, you'll need to escape it with \:

* [ ] \(Optional) Open a followup issue

## 测试strikethought

Parse ~~strikethrough~~ formatting

## fenced code

```python
def main():
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    args = sys.argv[1:]

    if not args:
        logging.debug('no file selected\n')
        sys.exit(1)

    filename = args[0]

    logging.debug("send " + filename + " to onenote")
    send_markdown(filename, markdown_processor_mode.ONENOTE)


# Main body
if __name__ == '__main__':
    main()
```

## 测试对theBrain文字颜色和底色的支持

some text  :{**Red on yellow**:(style="background-color:#ffff00;color:#aa0000"):}: with others :{**Yellow on red**:(style="background-color:#aa0000;color:#ffff00"):}: different.

some text  :{*Red on yellow*:(style="background-color:#ffff00;color:#aa0000"):}: with color

some text <span style="background-color:#ffff00;color:#aa0000">Red on yellow</span> with color