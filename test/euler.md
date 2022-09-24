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

### References

<span id='1'>[1]  [Euler's identity](https://en.wikipedia.org/wiki/Euler%27s_identity)   