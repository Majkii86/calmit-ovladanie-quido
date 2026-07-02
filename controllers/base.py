from abc import ABC, abstractmethod


class BaseGateController(ABC):
    @abstractmethod
    def get_status(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def open_gate(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def close_gate(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def reset_gate(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def fault_gate(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def offline_gate(self) -> dict:
        raise NotImplementedError