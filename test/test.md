# test title

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse eu venenatis quam. Vivamus euismod eleifend metus vitae pharetra. In vel tempor metus. Donec dapibus feugiat euismod. Vivamus interdum tellus dolor. Vivamus blandit eros et imperdiet auctor. Mauris sapien nunc, condimentum a efficitur non, elementum ac sapien. Cras consequat turpis non augue ullamcorper, sit amet porttitor dui interdum.

Sed laoreet luctus erat at rutrum. Proin velit metus, luctus in sapien in, tincidunt mattis ex. Praesent venenatis orci at sagittis eleifend. Nulla facilisi. In feugiat vehicula magna iaculis vehicula. Nulla suscipit tempor odio a semper. Donec vitae dapibus ipsum. Donec libero purus, convallis eu efficitur id, pulvinar elementum diam. Maecenas mollis blandit placerat. Ut gravida pellentesque nunc, in eleifend ante convallis sit amet.

Cells can vary in width and do not need to be perfectly aligned within columns. There must be at least three hyphens in each column of the header row.

| Command | Description |
| --- | --- |
| git status | List all new or modified files |
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

![x](<./test    image.jpeg>)

![x](<./test    image.jpeg> "image title")

![x](./test_image.jpg)

![x](./test_image.jpg "image title")

[link](http://google.com)

[link](<http://google.com/test page>)

[link](http://google.com "google")

[link](<http://google.com/test page> "google test page")

some [link](http://google.com) or image ![x](./haha.png) may be with title [link title](http://google.com "google"), images can also have title ![x](./hoho.png "hoho"), urls has spaces should use use [link](<http://google.com> "google") or img ![x](<./hehe.png> "hehe"). that is it

some text with {braces} {} in it

这**是(is)**一个苹果。

这*是(is)*一个苹果。

这**是[is]**一个苹果。

这**是【is】**一个苹果。

这**是《is》**一个苹果。

这**是<is>**一个苹果。

这**是（is）**一个苹果。

这**是**(**is**)一个苹果。

**心理学(psychology)**是关于**个体**的**行为**及**心智（mind）过程**的**科学研究**

**reference list:** Reference list entries should have a hanging indent of 0.5 in
 
中文:【不要加空格】
 
英文:[紧跟标点也不要加空格]

a.string,has;no:space?after   punctuation!another, string; has: space? after      puctuation! ok!

    test    multiple      space.

below is a code block:

    this         is      a   code block
	should not normalize

after code block

`````
hoho    xxx
````
      haha
`````test
`````

fenced code block is not touched

this is a block quote

> Sed laoreet luctus erat at rutrum. Proin velit metus, luctus in sapien in, tincidunt mattis ex. 
> Praesent venenatis orci at sagittis eleifend. Nulla facilisi. In feugiat vehicula magna iaculis