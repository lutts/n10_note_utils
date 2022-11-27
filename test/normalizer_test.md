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
# 测试一级标题

([1]p182s)


## 测试合并行

冥想 (meditation)是一种改变意识的形式，它通过获得深度的宁静状态而增强自我认识和幸福感口在专注冥想期间，人们把注意力集中在自己的呼吸和调节呼吸上. 采取某些身体姿势（如瑜伽姿势），使外部刺激减至最小，产生特定的心理表象，或什么都不想。而在专念冥想中，个体要学会如何让思想和回忆自由地穿行，而心理不对其做出反应。

Psychology's great strength is that it uses scientific observation to systematically answer questions about all sorts of behaviors. rats' behavior is observered. rats' behavior is measured. "what is psychology" psychology is

### markdown会被保留

```python
        inliner = css_inline.CSSInliner(remove_style_tags=True)
        inlined_html = inliner.inline(full_html)
        PutHtml(inlined_html, joined_markdown_text)
```

after code block

`````
hoho    xxx
````
      haha
`````test
`````

> Sed laoreet luctus erat at rutrum. Proin velit metus, luctus in sapien in, tincidunt mattis ex.
> Praesent venenatis orci at sagittis eleifend. Nulla facilisi. In feugiat vehicula magna iaculis
>
> a paragrah

| Command | Description |
| --- | --- |
| git status | List all new or modified files |
| git diff | To create a task list, preface list items with a hyphen and space followed by [ ]. To mark a task as complete, use [x].{nl}{nl}* [x] #739{nl}* [ ] [octo-org](https://github.com/octo-org/octo-repo/issues/740){nl}* [ ] Add delight to the experience when all tasks are complete : tada:{nl} {nl}If a task list item description begins with a parenthesis, you'll need to escape it with \: |

To create a task list, preface list items with a hyphen and space followed by [ ]. To mark a task as complete, use [x].

* [x] #739
* [ ] [octo-org](https://github.com/octo-org/octo-repo/issues/740)
* [ ] Add delight to the experience when all tasks are complete : tada:

If a task list item description begins with a parenthesis, you'll need to escape it with \:

* [ ] \(Optional) Open a followup issue

Parse ~~strikethrough~~ formatting

## 去掉中文字符之间，但中文和标点、英文、数字之间的空格保留

Hey Jane, 周末要不要一起吃早茶，叫上 Jennie 和 Jone, 预计花费 100 元

## 根据下文将中文引号转为英文引号

s1 = "some 'english' text"

s2 = "一些‘中文’文字"

s3 = 'some "english" text'

s4 = '一些“中文”文字'

## 根据上下文将中文括号转为英文括号

s5 = "some (english) text"

s6 = "一些（中文）文字"

## markdown加粗带括号中文的规范

* 这**是**(**is**)一个苹果。
* 这*是*(*is*)一个苹果。
* 这**是**[**is**]一个苹果。
* 这**是**【**is**】一个苹果。
* 这**是**《**is**》一个苹果。
* 这**是**<**is**>一个苹果。
* 这**是**(**is**)一个苹果。
* 这**是**(**is**)一个苹果。
* The third set of concerns relates to **divinity(神性)** vs. **神性**(**divinity**)测试:
* The third set of concerns relates to **divinity(神性)** vs. **神性(divinity)**。
* The third set of concerns relates to **divinity(神性)** vs. **神性(divinity)**
* The third set of concerns relates to **divinity(神性)** vs. **神性(divinity)** vs. others
* The third set of concerns relates to *divinity(神性)* vs. *神性*(*divinity*)测试:
* The third set of concerns relates to *divinity(神性)* vs. *神性(divinity)*。
* The third set of concerns relates to *divinity(神性)* vs. *神性(divinity)*
* The third set of concerns relates to *divinity(神性)* vs. *神性(divinity)* vs. others
* **心理学**(**psychology**)是关于**个体**的**行为**及**心智 (mind)过程**的**科学研究**
* **reference list:** Reference list entries should have a hanging indent of 0.5 in

## 空格的处理

### 一些英文标点符号后面要有空格

a. string, has; no: space? after punctuation! another, string; has: space? after puctuation! ok!

### 但如果这些英文禁点后面有其他标点符号或数字，则不加空格

中文:【不要加空格】

english:[english]

number:123

### 连续空格只保留一个，但行首的不动

    test multiple space.

        多个连续空格只保留一个，但行首的不动

* item1

  * item11
  * item12

* item2

  * item21
  * item22
    * item221
    * item222
* item3

### code block里的文字保留不变

```text
    this         is      a   code block
    should not normalize
```

### http Link和图片相关的markdown识别

![x](<./test    image.jpeg>)

![x](<./test    image.jpeg> "image title")

![x](./test_image.jpg)

![x](./test_image.jpg "image title")

[link](http://google.com)

[link](<http://google.com/test page>)

[link](http://google.com "google")

[link](<http://google.com/test page> "google test page")

complex_link = r'[Link text with [brackets] inside](http://www.example.com "My \"title\"")'

complex_img = r'![Link text with [brackets] inside](http://www.example.com/haha.png "My \"title\"")'

img_as_link_text = r'[![img](xxx/yyy.png)](http://google.com "My \"title\"")'

complex_link_angle = r'[Link text with [brackets] inside](<http://www.example.com> "My \"title\"")'

complex_img_angle = r'![Link text with [brackets] inside](<http://www.example.com/haha.png> "My \"title\"")'

img_as_link_text_angle = r'[![img](xxx/yyy.png)](<http://google.com> "My \"title\"")'

bad_link = '[link](<http://google. com "title")'

multiple_link_or_img = r'in one line [link](http://google.com) or image ![x](./haha.png) may be with title [link title](http://google.com "google"), images can also have title ![x](./hoho.png "hoho"), urls has spaces should use use [![img link](haha.png)](<http://google.com> "google") or img ![x](<./hehe.png> "hehe"). and there's some text with {braces} {} in it'

### table normalizer

haha
| hoho0 |
| :- |

---

| haha |
| :- |
| hoho1 hehe1 |

---

| haha |
| --------- |
| hoho2 |

---

| haha |
| -- |
| hoho3 |

---

| haha |
| - |
| hoho4 |

---

| haha |
| - |
| hoho5 |

---

| haha | hoho6 |
| -- | - |

---

| haha |
| - |
| - hoho7 |

---

| haha
- | hoho8

---

| haha |
| - |

---

| haha | hehe |
| - | | hoho10

---

haha | hoho
| --- | --- | hoho11

---

| haha | hehe |
| --- | --- |
| - |  |
| hoho12 |

---

| haha | hehe |
| --- | --- |
| hoho13 |  |
| * hoho14 |

---

| haha | hehe |
| --- | --- |
| hoho15 |  |
| * hoho16 |  |

---

| Variable |  |  |
| --- | --- | --- |
| Encodings | The way you categorize information about yourself, other people, events, and situations | As soon as Bob meets someone, he tries to figure out how wealthy he or she is. |
| Expectancies and beliefs | Your beliefs about the social world and likely outcomes for given actions in particular situations; your beliefs about your ability to bring outcomes about | Greg invites friends to the movies, but he never expects them to say "yes." |
| Affects | Your feelings and emotions, including physiological responses | Cindy blushes very easily. |
| Goals and values | The outcomes and affective states you do and do not value; your goals and life projects | Peter wants to be president of his college class. |
| Competencies and self-regulatory plans | The behaviors you can accomplish and plans for generating cognitive and behavioral outcomes | Jan can speak English, French, Russian, and Japanese and expects to work for the United Nations. |

([1]p182e)

[1]: <测试书名.pdf>
