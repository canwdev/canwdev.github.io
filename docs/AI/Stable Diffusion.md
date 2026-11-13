## 资源

- [【AI绘画】SD-WebUI 整合包 / 绘世启动器 / 训练器下载导航 （长期有效） - 秋葉aaaki](https://www.bilibili.com/read/cv31254871/)
- [Stable Diffusion web UI](https://github.com/AUTOMATIC1111/stable-diffusion-webui/)
- [AI绘画指南 stable diffusion webui （SD webui）如何设置与使用](https://www.tjsky.net/tutorial/488)

## 目录释义

在 Stable Diffusion 模型的 `models` 目录下，通常会包含几个子文件夹

- controlnet
- clip
- loras
- Stable-diffusion
- vae

以下是对这些文件夹的解释：

### `controlnet`

ControlNet 是一种用于条件生成的方法，它允许在生成过程中引入额外的控制信号。这使得模型可以根据特定的输入（如边缘图、关键点等）生成更加符合用户需求的图像。ControlNet 通常用于==增强图像生成的可控性==。

### `clip`

CLIP（Contrastive Language–Image Pretraining）模型与 Stable Diffusion 相辅相成。它是一种用于图像理解和文本理解的模型，它将图像和文本嵌入到同一个向量空间中。Stable Diffusion 通常会利用 CLIP 模型进行==文本到图像的同步==，帮助生成符合给定文本描述的图像。

### `loras`

> 模型滤镜

LoRA（Low-Rank Adaptation）是一种轻量级的==模型微调方法==，用于在不大量增加参数的情况下增强模型的能力。Lora 文件夹可能存储经过 LoRA 微调的模型，允许用户在特定任务上使用更专业的模型，这样的方法能在保持高效性的同时提高生成质量或多样性。

### `Stable-diffusion`

> 基础大模型

这个文件夹通常会包含 Stable Diffusion 的==基本模型文件==及其相关的配置。它是整个生成流程的核心部分，负责根据给定的输入生成图像。

### `vae`

变分自编码器（VAE）是 Stable Diffusion 中用于图像潜在空间表示的部分。VAE 将输入图像编码为潜在空间的向量表示，然后在这个潜在空间中进行操作，最后将生成的潜在向量解码回图像。这个过程有助于生成与训练数据相似的图像。

## ComfyUI 是什么

Stable Diffusion 是一个底层的图像生成模型，而 ComfyUI 是一个用户界面工具，使得用户能够更方便地与 Stable Diffusion 进行交互。ComfyUI 利用 Stable Diffusion 的功能，通过友好的界面增强用户体验。因此，ComfyUI 可以被视为 Stable Diffusion 的一个高级应用或前端表示。