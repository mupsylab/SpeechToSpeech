import sys
sys.path.append("./")

import time
import unittest
from dotenv import load_dotenv
load_dotenv()

class SpeedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._log = ""
        return super().setUpClass()
    
    @classmethod
    def tearDownClass(cls) -> None:
        print(cls._log)
        return super().tearDownClass()

    def _get_currtime(self):
        return int(time.time_ns() / 1000000)

    def _set_starttime(self):
        self.startTime = self._get_currtime()

    def logger(self, msg, reset_time: bool = False):
        if reset_time:
            self._set_starttime()
        use_time = self._get_currtime() - self.startTime
        SpeedTest._log += "\n%s: %s" % (use_time, msg)

    @unittest.skip("stop")
    def test_ollama(self):
        from core.llm import Chat
        module = __import__(f"core.llm.ollama", globals(), locals(), ["chat"])
        chat: Chat = module.chat

        isFirstChar = True
        isFirstSentence = True
        self.logger("Ollama耗时测试", True)
        for resp in chat([{"role": "user", "content": "你好"}]):
            if resp.type == "char" and isFirstChar:
                isFirstChar = False
                self.logger("首字符响应时间")
            if resp.type == "sentence" and isFirstSentence:
                isFirstSentence = False
                self.logger("首句子响应时间")

    @unittest.skip("stop")
    def test_chatgpt(self):
        from core.llm import Chat
        module = __import__(f"core.llm.chatgpt", globals(), locals(), ["chat"])
        chat: Chat = module.chat

        isFirstChar = True
        isFirstSentence = True
        self.logger("Chatgpt耗时测试", True)
        for resp in chat([{"role": "user", "content": "你好"}]):
            if resp.type == "char" and isFirstChar:
                isFirstChar = False
                self.logger("首字符响应时间")
            if resp.type == "sentence" and isFirstSentence:
                isFirstSentence = False
                self.logger("首句子响应时间")

    def test_sovits(self):
        from model.sovits import stream_io
        def generate_text():
            yield "你好"
            yield "接下来我要说一个很长很长的话"
            yield "请你仔细认真听哦"

        self.logger("VITS耗时测试", True)
        with open("model_pretrained/vits.wav", "wb") as f:
            for i, resp in enumerate(stream_io(generate_text())):
                f.write(resp)
                if i == 0:
                    # 首位不是tts的输出，而是文件头
                    continue
                self.logger("开始音频响应")

    def test_cosyvoice(self):
        from model.cosy import stream_io
        def generate_text():
            yield "你好"
            yield "接下来我要说一个很长很长的话"
            yield "请你仔细认真听哦"

        self.logger("CosyVoice耗时测试", True)
        with open("model_pretrained/cosy.wav", "wb") as f:
            for i, resp in enumerate(stream_io(generate_text())):
                f.write(resp)
                if i == 0:
                    # 首位不是tts的输出，而是文件头
                    continue
                self.logger("开始音频响应")

class CustomRunner(unittest.TextTestRunner):
    def run(self, test: unittest.TestSuite | unittest.TestCase):
        result = super().run(test)
        return result

if __name__ == "__main__":
    unittest.main(testRunner=CustomRunner())
