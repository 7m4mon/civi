from collections import deque


class CiviError(Exception):
    def __init__(self, code: int, message: str):
        self.code, self.message = code, message
        super().__init__(message)


class ErrorQueue:
    def __init__(self):
        self.items = deque()

    def add(self, error):
        if len(self.items) >= 32:
            self.items[-1] = CiviError(-350, "Queue overflow")
        else:
            self.items.append(error)

    def clear(self):
        self.items.clear()

    def pop(self):
        if not self.items:
            return '0,"No error"'
        e = self.items.popleft()
        return f'{e.code},"{e.message.replace(chr(34), chr(39))}"'
