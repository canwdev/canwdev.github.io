## 行内公式与块级公式

行内公式：$a^{x}$ $x^2$ $y_1 x_1 x_2$

块级公式：

$$a^2+b=c$$


## 常用字符

| 算式                          | LaTeX                       |
| ----------------------------- | --------------------------- |
| $\cdots$                      | \cdots                      |
| $^{\circ}$                    | ^{\circ}                    |
| $\pi$                         | \pi                         |
| $\infty$                      | \infty                      |
| $\theta$                      | \theta                      |
| $\in$                         | \in                         |
| $\notin$                      | \notin                      |
| $= \neq$                      | = \neq                      |
| $\pm$                         | \pm                         |
| $\times$                      | \times                      |
| $\cdot$                       | \cdot                       |
| $\div$                        | \div                        |
| $\le$$\ge$                    | \le \ge                     |
| $< >$                         | <>                          |
| $\angle$                      | \angle                      |
| $\because$ $\therefore$       | \because \therefore         |
| $( \big( \Big( \bigg( \Bigg($ | ( \big( \Big( \bigg( \Bigg( |

## 常用公式（用\$\$包含）

### 指数&下标

| 算式  | LaTeX |
| ----- | ----- |
| $x^2$ | x^2   |
| $x_2$ | x_2   |

### 分式

| 算式          | LaTeX       |
| ------------- | ----------- |
| $1/2$         | 1/2         |
| $\frac{1}{2}$ | \frac{1}{2} |

### 根号

| 算式          | LaTeX       |
| ------------- | ----------- |
| $\sqrt{2}$    | \sqrt{2}    |
| $\sqrt[3]{x}$ | \sqrt[3]{x} |

### 矢量

| 算式      | LaTeX   |
| --------- | ------- |
| $\vec{a}$ | \vec{a} |

### 积分

| 算式                    | LaTeX                 |
| ----------------------- | --------------------- |
| $\int{x}dx$             | \int{x}dx             |
| $\int_{1}^{2}{x}dx$     | \int_{1}^{2}{x}dx     |
| $\int\frac{x}{4+x^2}dx$ | \int\frac{x}{4+x^2}dx |

### 导数

| 算式                     | LaTeX                  |
| ------------------------ | ---------------------- |
| $f'(x)=xe^{\frac{x}{2}}$ | f'(x)=xe^{\frac{x}{2}} |
| $y''$                    | y''                    |

### 极限

| 算式                                      | LaTeX                                   |
| ----------------------------------------- | --------------------------------------- |
| $\lim{a+b}$                               | \lim{a+b}                               |
| $lim_{n\rightarrow+\infty}$               | lim_{n\rightarrow+\infty}               |
| $lim_{x\rightarrow1}\frac{e^x-e}{\ln(x)}$ | lim_{x\rightarrow1}\frac{e^x-e}{\ln(x)} |

### 累加

| 算式                    | LaTeX                 |
| ----------------------- | --------------------- |
| $\sum{a}$               | \sum{a}               |
| $\sum_{n=1}^{100}{a_n}$ | \sum_{n=1}^{100}{a_n} |

### 累乘

| 算式                    | LaTeX                 |
| ----------------------- | --------------------- |
| $\prod{x}$              | \prod{x}              |
| $\prod_{n=1}^{99}{x_n}$ | \prod_{n=1}^{99}{x_n} |

###  函数

| 算式          | LaTeX       |
| ------------- | ----------- |
| $\ln2$        | \ln2        |
| $\log_{2}8$   | \log_{2}8   |
| $\lg10$       | \lg10       |
| $\sin(x^2+1)$ | \sin(x^2+1) |

### 多行算式

$$
f(x)=\begin{cases} x,x<1\\ \frac{1}{1+x},x\ge1 \end{cases}
$$

$$
\begin{aligned}
   a&=b+c \\
   d+e&=f
\end{aligned}
$$

## 参考

- [Supported Functions - katex官方文档](https://katex.org/docs/supported.html)
- [Symbolab 数学求解器 - 可直接复制出 LaTeX]( https://zs.symbolab.com/ )
- [常用算式](https://blog.csdn.net/mingzhuo_126/article/details/82722455)
