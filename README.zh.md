# SpeechToSpeech

## 这是什么项目？
这是一个基于SensorVoice和GPT-SoVITS的实时语音对话基础框架，完美的支持流式生成，以及动态语音识别，甚至可以打断生成的音频！

> :warning: 由于当前项目是基础框架，旨在方便快速开发一个完整的项目，所以LLM目前采用ollama的api接口，并不涵盖在本项目当中。

## 为什么选择这个项目而不是GitHub上的其他类似项目？
由于conda等虚拟环境的开发，越来越多开发者不注重包直接的依赖关系，对于一个项目往往采取重建一个新环境的方式，然而这对硬盘空间不是很友好，所以开发本项目。
- 一个环境即可满足语音视频、语音生成的需求。
- 您也可以基于`api.py`快速开发一个额外的解决方案，甚至使用在线服务。
- 您可以随时用您的麦克风打断 LLM。

## 计划功能列表
- [x] 语音识别
- [x] 语音生成
- [x] 接入LLM进行聊天对话
- [ ] 能够使用不同情绪（模拟不同声音的方式）
- [ ] 接入FastGPT，能够调用外部函数
- [ ] 拓展成个人语音助手

> 欢迎有想法的小伙伴pull

## 额外要求
请确保你当前机器具有以下环境支持
- ffmpeg
- conda
- nodejs

## 安装使用
```shell
git clone https://www.github.com/mupsylab/speechtospeech.git
cd speechtospeech
```

对于使用，你还应该先手动下载额外的数据，包括
- 模型文件
- 用于克隆声音的音频
当然，这些你都可以从[OSS](https://insula.oss-cn-chengdu.aliyuncs.com/2024121001/STS_aio.zip)下载到。并放到项目根目录解压，记住`解压到`项目根目录。

启动后端，需要有一个python来运行api服务
```shell
conda create -n sts python==3.9.10 -y
conda activate sts
pip install -r requirements.txt

python main.py
```
随后API服务在默认启动在`0.0.0.0:8002`

最后，我们需要nodejs来运行前端。
```shell
cd ui
npm install
npm run dev
```
随后前端页面将绑定在`0.0.0.0:5173`上，浏览器访问`http://127.0.0.1:5173`即可

> 前端配置的默认API地址是`http://127.0.0.1:8002`，你可以在`ui/src/view/default.vue`进行修改


