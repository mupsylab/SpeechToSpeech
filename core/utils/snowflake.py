import time
import threading

__all__ = ["generate_snowflake_id"]

class SnowflakeIDGenerator:
    def __init__(self, machine_id: int):
        """
        初始化雪花算法 ID 生成器。

        :param machine_id: 机器ID (0 ~ 1023)
        """
        if machine_id < 0 or machine_id > 1023:
            raise ValueError("Machine ID must be between 0 and 1023.")

        self.machine_id = machine_id
        self.sequence = 0
        self.last_timestamp = -1

        # 起始时间戳（可以自定义，这里使用 2023-01-01 00:00:00）
        self.epoch = 1672531200000  # 2023-01-01 00:00:00 的毫秒数

        # 位长度
        self.timestamp_bits = 41
        self.machine_id_bits = 10
        self.sequence_bits = 12

        # 最大值
        self.max_sequence = (1 << self.sequence_bits) - 1

        # 移位量
        self.timestamp_shift = self.sequence_bits + self.machine_id_bits
        self.machine_id_shift = self.sequence_bits

        # 线程锁
        self.lock = threading.Lock()

    def _current_timestamp(self) -> int:
        """
        获取当前时间戳（毫秒）。
        """
        return int(time.time() * 1000)

    def _wait_for_next_millisecond(self, last_timestamp: int) -> int:
        """
        等待直到下一毫秒。
        """
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._current_timestamp()
        return timestamp

    def generate_id(self) -> int:
        """
        生成一个唯一的 ID。
        """
        with self.lock:
            timestamp = self._current_timestamp()

            # 如果当前时间小于上一次生成ID的时间，说明系统时钟回退
            if timestamp < self.last_timestamp:
                raise Exception("Clock moved backwards. Refusing to generate ID.")

            # 如果是同一毫秒内生成的，则递增序列号
            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.max_sequence
                # 如果序列号超出范围，则等待下一毫秒
                if self.sequence == 0:
                    timestamp = self._wait_for_next_millisecond(self.last_timestamp)
            else:
                # 不同毫秒内生成的，序列号重置
                self.sequence = 0

            self.last_timestamp = timestamp

            # 生成ID
            id = ((timestamp - self.epoch) << self.timestamp_shift) | \
                 (self.machine_id << self.machine_id_shift) | \
                 self.sequence
            return id

def generate_snowflake_id():
    return SnowflakeIDGenerator(0).generate_id()
