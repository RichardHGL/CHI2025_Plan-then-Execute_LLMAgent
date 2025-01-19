import copy

def generate_prompt(template: str, replace_dict: dict):
    prompt = copy.deepcopy(template)
    for k, v in replace_dict.items():
        prompt = prompt.replace(k, str(v))
    return prompt

import threading
import queue

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


class ThreadedGenerator:
    def __init__(self):
        self.queue = queue.Queue()

    def __iter__(self):
        return self

    def __next__(self):
        item = self.queue.get()
        if item is StopIteration: raise item
        return item

    def send(self, data):
        self.queue.put(data)

    def close(self):
        self.queue.put(StopIteration)

class ChainStreamHandler(StreamingStdOutCallbackHandler):
    def __init__(self, gen):
        super().__init__()
        self.gen = gen

    def on_llm_new_token(self, token: str, **kwargs):
        self.gen.send(token)
