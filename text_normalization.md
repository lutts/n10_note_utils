# 文本规范化方案

中文标点国标：GB/T 15834-2011

中英文混排及空格的使用好像没有国家标准

因为vs code根据文件类型自动切换字体，因此空格很难处理，所以在笔记处理的时候，没有理想的空格和标点规范化方案

不过可以考虑增加将选中的文本进行中文或英文规范化的命令，不过似乎也没有必要，情况仍然还是太复杂了

## 全角数字转换为半角

* 全角数字:０１２３４５６７８９     \uff10 - \uff19
* 半角为: 0123456789    \u0030 - \u0039
* 转换方案: 使用int转为数字再转为字符

## 空格规范

其实，不应该是“空格”规范，应该是“空白”规范，

* 中文
  * 中文之间不需要空格
  * 中英文之间增加空格
  * 中文与数字之间增加空格
  * 全角标点与其他字符之间不加空格
* 英文
  * 一些英文标点('.', ',', ';', ':', '?', '!')后面需要空格
  * 英文左括号后面不需要空格，前面需要空格
  * 英文右括号前面不需要空格，后面需要空格
  * 数字和英文的空格保持原文不变
  * 英文单词之间的空格需要空格
* 不能有连续的空格
* 正常空格：中文 english 加上 123 再加中文。
* 1/4空格：中文 english 加上 123 再加中文。

但完全按规范来，有时会出现不符合语义期望的情形，比如:

* 亚里士多德 (Aristotle) 如何如何
* 功利主义的功利译自英文词 utility，大致就是 useful（有用）的意思。

这两句话里的内容只是对前面内容的注释，过大的间隔不是我们所期望的

另外，像vs code这样不持标点挤压的，空格太宽，中文和英文之间如果增加空格，感觉上很不好

## unicode中的标点

* 中文标点分为了三处：
  * 和英文标点对应的部分在unicode的全角区
  * 引号在General Punctuation区(U+2000-U+206F)，因为中文引号在英文里称为smart quote
  * 其他一些特殊（比如书名号《》）在CJK Symbols and Punctuation(U+3000-U+303F)
* unicode中的Halfwidth and Fullwidth Forms区域是U+FF00 to U+FFEF
  * 全角区: u+FF01 to u+FF60
  * 半角区：u+FF61 to u+FFEE，主要是日韩字符
    * u+FF61是半角句号
    * U+FF64是半角顿号
    * U+FF65是Halfwidth Katakana(片假名) Middle Dot (垂直居中圆点)

## 括号

像下面这个例子，括号前后空白带来的“隔离感“个人认为非常影响阅读，思维会在这些大空白处停一下

所以在我（梁海）看来，中西文混排时应当根据该标点（the certain punctuation）所处的环境（environment、context 或 condition）来确定用哪一个书写系统（according to Glossary of Unicode Terms, a writing system is a set of rules for using one (or more) scripts to write a particular language）的标点样式。

## 关于1/4空格

能实现类似于标点搞压的效果

但是，这不是一个标准空格，如果仅仅为了显示效果就加入这样的空格，并不是很好

### 英文用来注释中文时

| 括号形式 | 示例 |
| --- | --- |
| 半角括号+1/4空格 | 亚里士多德 (Aristotle) 如何如何 |
| 仅半角括号       | 亚里士多德(Aristotle)如何如何 |
| 全角括号         | 亚里士多德（Aristotle）如何如何 |

english text

个人觉得`半角括号+1/4空格`更好看些，读的时候思维顺畅，半角空格形成一个`转折`，但又不是很突兀

### 中文用来注释英文时

| 括号形式 | 示例 |
| --- | --- |
| 半角括号+1/4空格 | 功利主义的功利译自英文词 utility，大致就是 useful (有用) 的意思。 |
| 仅半角括号       | 功利主义的功利译自英文词 utility，大致就是 useful(有用)的意思。 |
| 全角括号         | 功利主义的功利译自英文词 utility，大致就是 useful（有用）的意思。 |

仍然是`半角括号+1/4空格`的效果更好些

### 括号里的注释同时有英文和中文时

| 括号形式 | 示例 |
| --- | --- |
| 半角括号+1/4空格 | 柏拉图 (Plato, 公元前 4 世纪) 是古希腊人。 |
| 仅半角括号       | 柏拉图(Plato, 公元前 4 世纪)是古希腊人。 |
| 全角括号        | 柏拉图（Plato, 公元前 4 世纪）是古希腊人。 |

## 引号

英文的引号很特殊，无法区分左右

* 如果前后都是中文，则转换为中文引号
* 如果前后都是英文，则转换为英文引号
* 其他情况下，因为无法判断，保持不变

## 处理算法

三种环境：

* 中文环境：
  * 碰到一个中文字符后进入中文环境
  * 英文标点都转换为中文标点
* 非中文环境：
  * 碰到一个非中文字符后进入非中文环境
  * 中文标点都转换为英文标点
* 中文标点、英文标点、数字、空格不影响环境的判定
* 环境的结束：
  * 中文: `_sentence_end = '[{stops}][」﹂”』’》）］｝〕〗〙〛〉】]*'`
  * 非中文: stops换为英文，后面的字符只限于', ", ), ], }
* 不确定环境：1）碰到左括号；2）_sentence_end之后；
  * 碰到不确定环境时，需要停下来往前看，直到确定环境
  * 不确定环境时，是否需要对标点做转换需要看后面的内容

按照这个规则，始终是往前看的，不需要检查prev_char，理论上算法可以只需要一遍扫描，只在不确定环境的时候需要进行一次“嵌入式”向前扫描

```txt
中 ( 文  ---> 中 -> 随后的空格因为“中文环境”而被删除 -> ( -> 不确定环境开始 -> 开始往前看，直到确定环境 -> 确定为中文环境 -> 改为全角括号 -> 空格 -> 删除 --- 最终结果：中（文

中文english -> 中 -> 文 -> e -> 环境发生改变，增加空格 -> english , 最终结果: 中文 english

中文占比50%或更多 --- 中文占比 50％ 或更多
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

## InDesign标点挤压

简体中文模版中提供了适用于横排的三种基本标点挤压集。

一、开明式：在段落中，句末点号（句号、叹号、问号）采用全角，句中点号（逗号、 顿号、分号、冒号）及部分标号（引号、括号、书名号）等采用半角。

二、全角式：在段落中，除了两个相连的标点在一起时，前一标点采用半角外，所有 标点符号（除破折号、省略号等）在行中和行尾都采用全角。

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

全角空格，我们平时通过按键盘空格键得到的其实是半角空格，相当于一个小写的英文字母大小，定义上是2个半角空格的大小，在网页中却大约相当于3~4个半角空格的大小，而且它自身不易被左对齐。

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
