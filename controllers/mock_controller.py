import threading
import time

from fastapi import HTTPException

from controllers.base import BaseGateController


class MockGateController(BaseGateController):
    def __init__(self) -> None:
        self.state = "closed"
        self.last_action = None
        self.last_change = time.strftime("%Y-%m-%d %H:%M:%S")
        self.is_busy = False
        self.lock = threading.Lock()

    def _set_state(self, new_state: str, action: str | None = None) -> None:
        with self.lock:
            self.state = new_state
            self.last_action = action
            self.last_change = time.strftime("%Y-%m-%d %H:%M:%S")

    def _set_busy(self, value: bool) -> None:
        with self.lock:
            self.is_busy = value

    def get_status(self) -> dict:
        with self.lock:
            return {
                "state": self.state,
                "last_action": self.last_action,
                "last_change": self.last_change,
                "is_busy": self.is_busy,
            }

    def _delayed_state_change(self, target_state: str, delay_seconds: int, action: str) -> None:
        time.sleep(delay_seconds)
        self._set_state(target_state, action=action)
        self._set_busy(False)

    def open_gate(self) -> dict:
        snapshot = self.get_status()

        if snapshot["state"] == "offline":
            raise HTTPException(status_code=503, detail="Zariadenie je offline")

        if snapshot["state"] == "error":
            raise HTTPException(status_code=409, detail="Závora je v chybovom stave")

        if snapshot["is_busy"]:
            raise HTTPException(status_code=409, detail="Závora práve mení stav")

        if snapshot["state"] == "open":
            return {
                "ok": True,
                "action": "open",
                "state": "open",
                "detail": "Závora je už otvorená",
            }

        self._set_busy(True)
        self._set_state("moving", action="open")

        thread = threading.Thread(
            target=self._delayed_state_change,
            args=("open", 4, "open"),
            daemon=True,
        )
        thread.start()

        return {
            "ok": True,
            "action": "open",
            "state": "moving",
            "detail": "Prebieha otváranie závory",
        }

    def close_gate(self) -> dict:
        snapshot = self.get_status()

        if snapshot["state"] == "offline":
            raise HTTPException(status_code=503, detail="Zariadenie je offline")

        if snapshot["state"] == "error":
            raise HTTPException(status_code=409, detail="Závora je v chybovom stave")

        if snapshot["is_busy"]:
            raise HTTPException(status_code=409, detail="Závora práve mení stav")

        if snapshot["state"] == "closed":
            return {
                "ok": True,
                "action": "close",
                "state": "closed",
                "detail": "Závora je už zatvorená",
            }

        self._set_busy(True)
        self._set_state("moving", action="close")

        thread = threading.Thread(
            target=self._delayed_state_change,
            args=("closed", 4, "close"),
            daemon=True,
        )
        thread.start()

        return {
            "ok": True,
            "action": "close",
            "state": "moving",
            "detail": "Prebieha zatváranie závory",
        }

    def reset_gate(self) -> dict:
        self._set_busy(False)
        self._set_state("closed", action="reset")
        return {
            "ok": True,
            "detail": "Simulácia resetovaná",
            "gate": self.get_status(),
        }

    def fault_gate(self) -> dict:
        self._set_busy(False)
        self._set_state("error", action="fault")
        return {
            "ok": True,
            "detail": "Simulovaná porucha zariadenia",
            "gate": self.get_status(),
        }

    def offline_gate(self) -> dict:
        self._set_busy(False)
        self._set_state("offline", action="offline")
        return {
            "ok": True,
            "detail": "Simulovaná nedostupnosť zariadenia",
            "gate": self.get_status(),
        }