# SpeechToSpeech

## What is this project?
This is a real-time speech-to-speech conversation framework based on SensorVoice and GPT-SoVITS. It perfectly supports streaming generation, dynamic speech recognition, and even the ability to interrupt generated audio!

> :warning: Since this project is a foundational framework aimed at facilitating the rapid development of a complete project, the LLM currently uses the Ollama API interface and is not included within this project.

## Why choose this project over other similar projects on GitHub?
With the development of virtual environments like Conda, more and more developers are not focusing on direct package dependencies. Instead, they often create a new environment from scratch for a project, which is not very disk space-friendly. Therefore, this project was developed.

- A single environment can satisfy the needs for audio, video, and speech generation.
- You can also quickly develop an additional solution based on `api.py`, or even use online services.
- You can interrupt the LLM at any time using your microphone.

## Planned Feature List
- [x] Speech recognition
- [x] Speech generation
- [x] Integration of LLM for chat conversations
- [ ] Ability to use different emotions (simulating different voices)
- [ ] Integration of FastGPT to enable external function calls
- [ ] Expansion into a personal voice assistant

> Contributions are welcome! Feel free to submit pull requests if you have ideas.

## Additional Requirements
Please ensure your machine has the following environment support:
- ffmpeg
- Conda
- Node.js

## Installation and Usage
```shell
git clone https://www.github.com/mupsylab/speechtospeech.git
cd speechtospeech
```

For usage, you should also manually download additional data, including:
- Model files
- Audio for voice cloning

Of course, you can download these from the [provided sources](https://insula.oss-cn-chengdu.aliyuncs.com/2024121001/STS_aio.zip). Extract them into the project root directory, and remember to extract them directly into the project root.

### Starting the Backend
You need Python to run the API service:
```shell
conda create -n sts python==3.9.10 -y
conda activate sts
pip install -r requirements.txt

python main.py
```
The API service will start by default at `0.0.0.0:8002`.

### Starting the Frontend
Finally, you need Node.js to run the frontend:
```shell
cd ui
npm install
npm run dev
```
The frontend page will be accessible at `0.0.0.0:5173`. Open your browser and navigate to [http://127.0.0.1:5173](http://127.0.0.1:5173).

> The frontend is configured by default to use the API address `http://127.0.0.1:8002`. You can modify this in `ui/src/view/default.vue`.
