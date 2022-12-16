# 文本规范化方案

中文标点国标：GB/T 15834-2011

中英文混排及空格的使用好像没有国家标准

## 全角数字转换为半角

* 全角数字：`０１２３４５６７８９` \uff10 - \uff19
* 半角为：0123456789 \u0030 - \u0039
* 转换方案：使用 int 转为数字再转为字符

## 空格规范

其实，不应该是“空格”规范，应该是“空白”规范，

* 中文
  * 中文之间不需要空格
  * 中英文之间增加空格
  * 中文与数字之间增加空格
  * 全角标点与其他字符之间不加空格
* 英文
  * 一些英文标点 `('.', ',', ';', ':', '?', '!')` 后面需要空格
  * 英文左括号后面不需要空格，前面需要空格
  * 英文右括号前面不需要空格，后面需要空格
  * 数字和英文的空格保持原文不变
  * 英文单词之间的空格需要空格
* 不能有连续的空格
* 正常空格：中文 english 加上 123 再加中文。
* 1/4 空格：`中文 english 加上 123 再加中文。`

但完全按规范来，有时会出现不符合语义期望的情形，比如：

```text
* 亚里士多德（Aristotle）如何如何
* 功利主义的功利译自英文词 utility，大致就是 useful（有用）的意思。
```

这两句话里的内容只是对前面内容的注释，中文括号过大的间隔不是我们所期望的

## unicode 中的标点

* 中文标点分为了三处：
  * 和英文标点对应的部分在 unicode 的全角区
  * 引号在 General Punctuation 区 (U+2000-U+206F), 因为中文引号在英文里称为 smart quote
  * 其他一些特殊 (比如书名号《》) 在 CJK Symbols and Punctuation (U+3000-U+303F)
* unicode 中的 Halfwidth and Fullwidth Forms 区域是 U+FF00 to U+FFEF
  * 全角区：u+FF01 to u+FF60
  * 半角区：u+FF61 to u+FFEE, 主要是日韩字符
    * u+FF61 是半角句号
    * U+FF64 是半角顿号
    * U+FF65 是 Halfwidth Katakana (片假名) Middle Dot (垂直居中圆点)

## 括号

像下面这个例子，括号前后空白带来的“隔离感“个人认为非常影响阅读，思维会在这些大空白处停一下

```text
所以在我（梁海）看来，中西文混排时应当根据该标点（the certain punctuation）所处的环境（environment、context 或 condition）来确定用哪一个书写系统（according to Glossary of Unicode Terms, a writing system is a set of rules for using one (or more) scripts to write a particular language）的标点样式。
```

## 关于 1/4 空格

能实现类似于标点挤压的效果

但是，这不是一个标准空格，如果仅仅为了显示效果就加入这样的空格，并不是很好

### 英文用来注释中文时

| 括号形式 | 示例 |
| --- | --- |
| 半角括号+1/4 空格 | `亚里士多德 (Aristotle) 如何如何` |
| 半角括号+正常空格 | `亚里士多德 (Aristotle) 如何如何` |
| 仅半角括号 | `亚里士多德(Aristotle)如何如何` |
| 全角括号 | `亚里士多德（Aristotle）如何如何` |

个人觉得 `半角括号+1/4空格` 更好看些，读的时候思维顺畅，半角空格形成一个 `转折`, 但又不是很突兀

### 中文用来注释英文时

| 括号形式 | 示例 |
| --- | --- |
| 半角括号+1/4 空格 | `功利主义的功利译自英文词 utility，大致就是 useful (有用) 的意思。` |
| 半角括号+正常空格 | `功利主义的功利译自英文词 utility，大致就是 useful (有用) 的意思。` |
| 仅半角括号 | `功利主义的功利译自英文词 utility，大致就是 useful(有用)的意思。` |
| 全角括号 | `功利主义的功利译自英文词 utility，大致就是 useful（有用）的意思。` |

仍然是 `半角括号+1/4空格` 的效果更好些

### 括号里的注释同时有英文和中文时

| 括号形式 | 示例 |
| --- | --- |
| 半角括号+1/4 空格 | `柏拉图 (Plato, 公元前 4 世纪) 是古希腊人。` |
| 半角括号+正常空格 | `柏拉图 (Plato, 公元前 4 世纪) 是古希腊人。` |
| 仅半角括号 | `柏拉图(Plato, 公元前 4 世纪)是古希腊人。` |
| 全角括号 | `柏拉图（Plato, 公元前 4 世纪）是古希腊人。` |

## 我的方案

* 强制转为半角的
  * 全角数字转换为半角
  * 小括号、中括号、大括号、尖括号都转为对应的英文括号
    * 因为中文的这些括号的留白实在是太大了，与前后文字造成很大的隔离感，读的时候脑子都会停顿一下
  * 全角的“/”和“|”都转为英文的
* 中文
  * 中文之间不需要空格
  * 中英文之间增加空格
  * 中文与数字之间增加空格
  * 全角标点与其他字符之间不加空格
* 英文
  * 一些英文标点 `('.', ',', ';', ':', '?', '!')` 后面需要空格
  * 英文左括号后面不需要空格，前面需要空格
  * 英文右括号前面不需要空格，后面需要空格
  * 数字和英文的空格保持原文不变
  * 英文单词之间需要空格
  * 数字之间的点或逗号或冒号左右可以没有空格，但如果有，则将点或逗号视为平常的标点
* 标点之间不加空格
* 不能有连续的空格
* 标点
  * 中文标点只对“《标点符号用法》GB/T 15834-2011”标准里的部分标点进行全角/半角转换处理
    * 根据环境进行全角/半角转换的包括：`句号 (。)，问号 (？)，叹号 (！)，逗号 (，)，分号 (；)，冒号 (：)，下横('\uFF3F')`
    * 不转换
      * 分隔号 (`／|`): 强制转为英文，即半角的
      * 顿号：中文独有，有半角的形式 U+FF64
      * 引号：后面详述
      * 括号：后面详述
      * 破折号，省略号：比较特殊，暂不处理
      * 连接号：不处理，短横不好处理，markdown 的 strikethrough 用到了波浪号
      * 间隔号：中英通用，无需处理
  * 连续中文标点：除最后一个外，其他的转为半角
    * 半角句号：u+FF61
  * 引号：
    * 关于引号**前后**的空格
      * 引号可能嵌套，嵌套的时候有人会在不同的引号间加空格
      * 所以，如果前后有空格，则保留，如果没有，也不自动添加
    * 引号不做全角/半角转换
      * 英文引号无法确定左右，没法转换
      * 中文引号在英语里被称为 smart quote, 因此也不进行转换，保留为 smart quote
    * 比较特殊的是右单引号，这可能是英语里的 contraction 或者所有格 (possessive)
      * 右单引号要处理的主要原因是很多常用字体的右单引号都太宽了，能把"it's"这样的 t 和 s 隔得老远，例如微软雅黑
      * contraction 常见形式后面详细说明
      * 所有格两种形式：
        * xxx's: 要判断的话，就是单引号后面跟着一个孤零零的 s
        * xxx': 这个就很难判断了，因为也有可能真是引号

总结一下就是：

* 无法确定是全角还是半角的字符、标点，一律按半角处理
* 平常用的空格是半角字符
* 全角之间不需要空格，严格执行
* 半角之间不需要空格，但如果有，也不删除
* 全角、半角之间需要空格，但与某些半角标点之间的关系有点暧昧
* 连续中文标点：除最后一个外，其他的转为半角
* 不能有连续的空格
* 标点之间不加空格，但有些特殊情况要考虑
* 特殊情况：完全不考虑全角/半角
  * 全角标点前后都不能有空格，
  * 全角与不在转换表之外的半角标点之间可以没有空格，如果有，保留，如果没有，不自动添加
  * 左括号：
    * 前面需要空格，但如果前面是标点，也可以没有空格
    * 后面不需要空格，但如果是“[ ]”这样的，则空格会保留
  * 右括号：
    * 前面不需要空格，只有“[ ]”中的会保留
    * 后面需要空格，但如果后面是标点，也可以没有空格
  * 半角语境下的右单引号需要特殊处理
  * 英文标点 `('.', ',', ';', ':', '?', '!')` 前面不需要空格，后面需要空格，除非
    * 点，逗号，冒号：如果前后都是数字，则不自动添加空格
    * 如果后面是标点，则不需要空格
  * 引号：如果前后有空格，则保留，如果没有，也不自动添加，但也有例外：
    * 左引号后面如果不是标点，则不需要空格
    * 右引号前面如果不是标点，则不需要空格
  * 加号和减号：因为有可能是正数和负数的表示，所以允许前面有标点，但前提是后面跟着的是数字
  * 反斜杠 (\\)：因为这个字符主要是用于转义，因此它对前后空格的处理取决于它后面的字符

语境

* 全角语境：
  * 碰到全角字符后进入全角语境
  * 碰到 `_sentence_end` 或者非全角、非标点即退出
* 半角环境：
  * 碰到非全角、非标点字符后进入半角语境
  * 碰到 `_sentence_end` 或者全角字符即退出
* `_sentence_end = '[.?!｡。？！][」﹂”』’》）］｝)\]}>〕〗〙〛〉】]*'`
  * 英文点前后如果都是数字，则不视为句子的结尾
* 不确定语境：
  * 定义：`_sentence_end` 和下一个非标点字符之间
  * 如果下一个非标点字符是中文，则不确定环境为中文环境
  * 如果下一个非标点字符是英文，则不确定环境为英文环境
  * 如果后面全是标点，则不确定环境由前一个环境决定
  * 如果一句话全是标点，那就什么也不做，原样返回
* 如果在全角语境，则半角标点转为全角标点
* 如果在半角语境，则全角标点转为半角标点

示例：

* 亚里士多德 (Aristotle) 如何如何
* 功利主义的功利译自英文词 utility, 大致就是 useful (有用) 的意思。
* 柏拉图 (Plato, 公元前 4 世纪) 是古希腊人。
* 中文“english”

所以在我 (梁海) 看来，中西文混排时应当根据该标点 (the certain punctuation) 所处的环境 (environment、context 或 condition) 来确定用哪一个书写系统 (according to Glossary of Unicode Terms, a writing system is a set of rules for using one (or more) scripts to write a particular language) 的标点样式。

### contraction 常见形式

* 'm for am
* 's for is, has
* 're for are
* 've for have
* 'd for had
* 'll for will
* 't for isn't, haven't
* o'clock for *of the clock*
* Y'all for You all

Y'all 的情形比较难区分，不考虑

### 处理算法

```text
if 全角数字:
  转为半角数字

if 中文字符:
  中文环境=True
  if 环境改变 并且 前一个字符不是空格:
    增加空格
elif 英文字符:
  英文环境=True
  if 环境改变 并且 前一个字符不是空格:
    增加空格
elif 小括号、中括号、大括号:
  转为半角
  if 左括号:
    if 前面没空格：
      前面加空格
  else:
    后面加空格
    if 前面有空格：
      删除
elif 句号、问号、感叹号:
  sentence_end_env = True
elif sentence_end_env:
  if char in _sentence_end:
      仍然位于sentence_end中
  else:
    不确定环境
    往前扫描，直到遇到中文或英文字符，从而确定该使用的环境
    如果扫描到行尾都没遇到中文或英文字符，沿用当前环境
elif 空格:
  if 前后都是标点：
    删除
  if 前一个字符是空格：
    删除
  if 前后都是中文:
    删除
  if 前面是全角标点：
    删除
  if 后面是全角标点:
    删除
  if 前面是左括号:
    删除
  if 后面是右括号:
    删除
elif 英文标点('.', ',', ';', ':', '?', '!'):
  后面增加一个空格
elif 中文右引号:
  如果后面的字符串是：['d', 'm', 's', 't', 'll', 're', 've'] + 空格，则将中文右引号转换为英文单引号
elif // 其他标点
  根据当前环境转换全角或半角
  if 全角标点 并且 前一个字符是空格:
    删除前一个空格
```

```python
    en_stop_to_cn = {
        '!': '\uFF01',
        '?': '\uFF1F',
        '.': '\u3002',
    }

    en_to_cn_punc_map = {
        '#': '\uFF03',
        '$': '\uFF04',
        '%': '\uFF05',
        '&': '\uFF06',
        '*': '\uFF0A',
        '+': '\uFF0B',
        ',': '\uFF0C',
        '-': '\uFF0D',
        '/': '\uFF0F',
        ':': '\uFF1A',
        ';': '\uFF1B',
        '=': '\uFF1D',
        '@': '\uFF20',
        '\\': '\uFF3C',
        '^': '\uFF3E',
        '_': '\uFF3F',
        '`': '\uFF40',
        '|': '\uFF5C',
        '~': '\uFF5E',
    }

    left_en_punc_to_cn = {
        '<': '\u3008',
        '(': '\uFF08',
        '[': '\uFF3B',
        '{': '\uFF5B',
    }

    right_en_punc_to_cn = {
        '>': '\u3009',
        ')': '\uFF09',
        ']': '\uFF3D',
        '}': '\uFF5D',
    }

    cn_to_en_punc_map = {
        '\uFF03': '#',
        '\uFF04': '$',
        '\uFF05': '%',
        '\uFF06': '&',
        '\uFF0A': '*',
        '\uFF0B': '+',
        '\uFF0C': ',',
        '\uFF0D': '-',
        '\uFF0F': '/',
        '\uFF1A': ':',
        '\uFF1B': ';',
        '\uFF1D': '=',
        '\uFF20': '@',
        '\uFF3C': '\\',
        '\uFF3E': '^',
        '\uFF3F': '_',
        '\uFF40': '`',
        '\uFF5C': '|',
        '\uFF5E': '~',
    }

    cn_stop_to_en = {
        '\uFF01': '!',
        '\uFF1F': '?',
        '\uFF61': '.',
        '\u3002': '.',
    }

    left_cn_punc_to_en = {
        '\uFF08': '(',
        '\u3008': '<',
        '\uFF3B': '[',
        '\uFF5B': '{',
        '\u2018': "'",
        '\u201c': '"',
    }

    right_cn_punc_to_en = {
        '\uFF09': ')',
        '\u3009': '>',
        '\uFF3D': ']',
        '\uFF5D': '}',
        '\u2019': "'",
        '\u201d': '"',
    }
```

```typescript
        let basicLatin = '[0-9A-Za-z]';
        let latin1Supplement = '[\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u00FF]';
        let latinExtendedA = '[\\u0100-\\u017F]';
        let latinExtendedB = '[\\u0180-\\u01BF\\u01C4-\\u024F]';
        let halfwidthChars = 
            [basicLatin, latin1Supplement, latinExtendedA, latinExtendedB].join('|');

        let hiragana = '[\\u3040-\\u309F]';
        let katakana = '[\\u30A0-\\u30FF]';
        let cjkUnifiedIdeographs = '[\\u4E00-\\u9FFF]';
        let cjkUnifiedIdeographsA = '[\\u3400-\\u4DBF]';
        let cjkUnifiedIdeographsB = '[\\ud840-\\ud868][\\udc00-\\udfff]|\\ud869[\\udc00-\\uded6]';
        let fullwidthChars = 
            [hiragana, katakana, cjkUnifiedIdeographs,
                cjkUnifiedIdeographsA, cjkUnifiedIdeographsB].join('|');
```

## InDesign 标点挤压

简体中文模版中提供了适用于横排的三种基本标点挤压集。

一、开明式：在段落中，句末点号 (句号、叹号、问号) 采用全角，句中点号 (逗号、顿号、分号、冒号) 及部分标号 (引号、括号、书名号) 等采用半角。

二、全角式：在段落中，除了两个相连的标点在一起时，前一标点采用半角外，所有标点符号 (除破折号、省略号等) 在行中和行尾都采用全角。

三、全角式+行尾半角：在全角式的基础上，排在每行行尾的标点都采用半角，以使版口的文字看起来更为整齐。

## get unicode point of charactor

```python
hex(ord('c'))
```

## Regular and Unusual Space Characters

unicode Space Separator, or Unicode Zs general category

## Regular Space Characters

[U+0020 SPACE](https://unicode-explorer.com/c/0020)

This is the regular space character as produced by pressing the space bar of your keyboard.

[U+00A0 NO-BREAK SPACE](https://unicode-explorer.com/c/00A0)

A fixed space that prevents an automatic line break at its position. Abbreviation: NBSP

[U+2000 EN QUAD](https://unicode-explorer.com/c/2000)

A 1 en (= 1/2 em) wide space, where 1 em is the height of the current font.

[U+2001 EM QUAD](https://unicode-explorer.com/c/2001)

A 1 em wide space, where 1 em is the height of the current font.

[U+2002 EN SPACE](https://unicode-explorer.com/c/2002)

A 1 en (= 1/2 em) wide space, where 1 em is the height of the current font.

[U+2003 EM SPACE](https://unicode-explorer.com/c/2003)

A 1 em wide space, where 1 em is the height of the current font.

[U+2004 THREE-PER-EM SPACE](https://unicode-explorer.com/c/2004)

A 1/3 em wide space, where 1 em is the height of the current font. "Thick Space".

[U+2005 FOUR-PER-EM SPACE](https://unicode-explorer.com/c/2005)

A 1/4 em wide space, where 1 em is the height of the current font. "Mid Space".

[U+2006 SIX-PER-EM SPACE](https://unicode-explorer.com/c/2006)

A 1/6 em wide space, where 1 em is the height of the current font.

[U+2007 FIGURE SPACE](https://unicode-explorer.com/c/2007)

A space character that is as wide as fixed-width digits. Usually used when typesetting vertically aligned numbers.

[U+2008 PUNCTUATION SPACE](https://unicode-explorer.com/c/2008)

A space character that is as wide as a period (".").

[U+2009 THIN SPACE](https://unicode-explorer.com/c/2009)

A 1/6 em - 1/4 em wide space, where 1 em is the height of the current font.

[U+200A HAIR SPACE](https://unicode-explorer.com/c/200A)

Narrower than the "THIN SPACE", usually the thinnest space character.

[U+202F NARROW NO-BREAK SPACE](https://unicode-explorer.com/c/202F)

A narrow form of a no-break space, typically the width of a "THIN SPACE". Abbreviation: NNBSP.

[U+205F MEDIUM MATHEMATICAL SPACE](https://unicode-explorer.com/c/205F)

A 4/18 em wide space, where 1 em is the height of the current font. Usually used when typesetting mathematical formulas.

[U+3000 IDEOGRAPHIC SPACE](https://unicode-explorer.com/c/3000)

全角空格，我们平时通过按键盘空格键得到的其实是半角空格，相当于一个小写的英文字母大小，定义上是 2 个半角空格的大小，在网页中却大约相当于 3~4 个半角空格的大小，而且它自身不易被左对齐。

全角空格一般适用于在强制性左对齐的情况下需要居中或者在其他特定位置的时候。一些乱码字中也会出现全角空格。

## Regular Space Characters with Zero Width

[U+200B ZERO WIDTH SPACE](https://unicode-explorer.com/c/200B)

Literally a zero-width space character.

[‌U+200C ZERO WIDTH NON-JOINER](https://unicode-explorer.com/c/200C)

When placed between two characters that would otherwise be connected into a ligature, a ZWNJ causes them to be printed in their final and initial forms, respectively.

[‍U+200D ZERO WIDTH JOINER](https://unicode-explorer.com/c/200D)

When placed between two characters that would otherwise not be connected, a ZWJ causes them to be printed in their connected forms (ligature). Also used to join emoji with modifier characters.

[U+2060 WORD JOINER](https://unicode-explorer.com/c/2060)

A zero width non-breaking space. Abbreviation: WJ.

[U+FEFF ZERO WIDTH NO-BREAK SPACE](https://unicode-explorer.com/c/FEFF)

The zero width no-break space (ZWNBSP) is a deprecated use of the Unicode character at code point U+FEFF. Character U+FEFF is intended for use as a Byte Order Mark (BOM) at the start of a file. However, if encountered elsewhere, it should, according to Unicode, be treated as a "zero width no-break space". The deliberate use of U+FEFF for this purpose is deprecated as of Unicode 3.2, with the word joiner strongly preferred.

## Non-Space Characters that Act Like Spaces

The following characters are probably the most interesting: they act like regular space characters, but are typically not considered as such. Because of this, they can often be used in places where a single (regular) space character is not allowed (e.g. as a Youtube video title, in nick names in popular games, etc.).

[U+180E MONGOLIAN VOWEL SEPARATOR](https://unicode-explorer.com/c/180E)

The MVS is a word-internal thin whitespace that may occur only before the word-final vowels U+1820 MONGOLIAN LETTER A and U+1821 MONGOLIAN LETTER E. It determines the specific form of the character preceding it, selects a special variant shape of these vowels, and produces a small gap within the word. It is no longer classified as space character (i.e. in Zs category) in Unicode 6.3.0, even though it was in previous versions of the standard.

[U+2800 BRAILLE PATTERN BLANK](https://unicode-explorer.com/c/2800)

The Braille pattern "dots-0", also called a "blank Braille pattern", is a 6-dot or 8-dot braille cell with no dots raised. It is represented by the Unicode code point U+2800, and in Braille ASCII with a space. In all Braille systems, the Braille pattern dots-0 is used to represent a space or the lack of content. In particular some fonts display the character as a fixed-width blank. However, the Unicode standard explicitly states that it does not act as a space.

[U+3164 HANGUL FILLER](https://unicode-explorer.com/c/3164)

The Hangul Filler character is used to introduce eight-byte Hangul composition sequences and to stand in for an absent element (usually an empty final) in such a sequence. Unicode includes the Wansung code Hangul Filler in the Hangul Compatibility Jamo block for round-trip compatibility, but uses its own system (with its own, differently used, filler characters) for composing Hangul.

## Visible Space Characters

[␠ U+2420 SYMBOL FOR SPACE](https://unicode-explorer.com/c/2420)

[␢ U+2422 BLANK SYMBOL](https://unicode-explorer.com/c/2422)

[␣ U+2423 OPEN BOX](https://unicode-explorer.com/c/2423)
