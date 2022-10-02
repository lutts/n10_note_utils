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
### Abstract

Euler's identity makes a valid formula out of five mathematical constants.

![x](test_image.jpg)

another img

![x](<./test    image.jpeg>)

web image:

![x](https://www.ncl.ucar.edu/Images/NCL_NCAR_NSF_banner.png)

## 1. Introduction

Euler's identity is often cited as an example of deep mathematical beauty.
Three basic arithmetic operations occur exactly once and combine five fundamental mathematical constants [[1](#1)].

## 2. The Identity

Starting from Euler's formula $ e^{ix}=\cos x + i\sin x $ for any real number $x$, we get to Euler's identity with the special case of $x = \pi$

$$e^{i\pi}+1=0\,.$$ (1)

The arithmetic operations *addition*, *multiplication* and *exponentiation* combine the fundamental constants 

$$\tag{lo} z = 3$$

* the additive identity $0$.
* the multiplicative identity $1$.
* the circle constant $\pi$.
* Euler's number $e$.
* the imaginary constant $i$.

## 3. Conclusion

It has been shown, how Euler's identity makes a valid formula from $A_1, A_2, \dotsc$ five mathematical constants.

$$\frac{1}{\left(\sqrt{\phi\sqrt{5}}-\phi\right)e^{\frac{2}{5}\pi}}=
 1+\frac{e^{-2\pi}} {
   1+\frac{e^{-4\pi}} {
     1+\frac{e^{-6\pi}} {
       1+\frac{e^{-8\pi}} {
         1+\cdots
       }
     }
   }
}$$

another

$$
\begin{equation}\tag{name}\begin{split}
H_c&=\frac{1}{2n} \sum^n_{l=0}(-1)^{l}(n-{l})^{p-2}\sum_{l _1+\dots+ l _p=l}\prod^p_{i=1} \binom{n_i}{l _i}\\
&\quad\cdot[(n-l )-(n_i-l _i)]^{n_i-l _i}\cdot
\Bigl[(n-l )^2-\sum^p_{j=1}(n_i-l _i)^2\Bigr].
\end{split}\end{equation}
$$

### Overriding default mathematical styles

The canonical example is taken from page 142 of the TeXBook

```
a_0+{1\over a_1+
      {1\over a_2+
        {1 \over a_3 + 
           {1 \over a_4}}}}
```

by default, this is typeset as:

$$
a_0+{1\over a_1+
      {1\over a_2+
        {1 \over a_3 + 
           {1 \over a_4}}}}
$$

The default typesetting style can be amended by using the \displaystyle command:

```
a_0+{1\over\displaystyle a_1+
      {1\over\displaystyle a_2+
        {1 \over\displaystyle a_3 + 
           {1 \over\displaystyle a_4}}}}
```

yielding

$$
a_0+{1\over\displaystyle a_1+
      {1\over\displaystyle a_2+
        {1 \over\displaystyle a_3 + 
           {1 \over\displaystyle a_4}}}}
$$

Here’s another example which demonstrates the effect of \textstyle, \scriptstyle and \scriptscriptstyle:

```
\begin{eqnarray*}
f(x) = \sum_{i=0}^{n} \frac{a_i}{1+x} \\
\textstyle f(x) = \textstyle \sum_{i=0}^{n} \frac{a_i}{1+x} \\
\scriptstyle f(x) = \scriptstyle \sum_{i=0}^{n} \frac{a_i}{1+x} \\
\scriptscriptstyle f(x) = \scriptscriptstyle \sum_{i=0}^{n} \frac{a_i}{1+x}
\end{eqnarray*}
```

which renders as

$$
\begin{array}{c}
\displaystyle f(x) = \textstyle \sum_{i=0}^{n} \frac{a_i}{1+x} \\
\textstyle f(x) = \textstyle \sum_{i=0}^{n} \frac{a_i}{1+x} \\
\scriptstyle f(x) = \scriptstyle \sum_{i=0}^{n} \frac{a_i}{1+x} \\
\scriptscriptstyle f(x) = \scriptscriptstyle \sum_{i=0}^{n} \frac{a_i}{1+x}
\end{array}
$$


### Spacing in math mode

$$
S = \{ z \in \mathbb{C}\, |\, |z| < 1 \} \quad \textrm{and} \quad S_2=\partial{S}
$$

$$
\begin{align*}
f(x) &= x^2\! +3x\! +2 \\
f(x) &= x^2+3x+2 \\
f(x) &= x^2\, +3x\, +2 \\
f(x) &= x^2\: +3x\: +2 \\
f(x) &= x^2\; +3x\; +2 \\
f(x) &= x^2\ +3x\ +2 \\
f(x) &= x^2\quad +3x\quad +2 \\
f(x) &= x^2\qquad +3x\qquad +2
\end{align*}
$$

$$
\begin{align*}
3ax+4by=5cz\\
3ax<4by+5cz
\end{align*}
$$


### Arrays

Arrays line items up in columns. Here are some basic steps for making arrays

* Type \begin{array}.
* Use an argument to describe how you want your table to be justified. Immediately following the \begin{array} command, add a set of brackets.

    Inside the brackets, use the letters r (right), c (center), and l (left) for each column to describe how it will be formatted.

    For example, if you have a three-column array and you want the text to be right-justified in the first column, centered in the second, and left-justified in the third, the argument would be {rcl}.
* Type your data, using & to separate columns and \\ to move to the next row.
* End the array with \end{array}.

$$
\begin{array}{lcl}
f(x) & = & (a+b)^2 \\
& = & a^2+2ab+b^2 \\
\end{array}
$$

### References

<span id='1'>[1]  [Euler's identity](https://en.wikipedia.org/wiki/Euler%27s_identity)   