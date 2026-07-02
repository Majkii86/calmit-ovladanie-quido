import time
import requests
import xml.etree.ElementTree as ET
from fastapi import HTTPException

from config import (
    QUIDO_IP,
    REQUEST_TIMEOUT,
    PULSE_SECONDS,
    GATE1_OUTPUT_OPEN_ID,
    GATE1_OUTPUT_CLOSE_ID,
    GATE1_INPUT_OPEN_ID,
    GATE1_INPUT_CLOSED_ID,
    GATE2_OUTPUT_OPEN_ID,
    GATE2_OUTPUT_CLOSE_ID,
    GATE2_INPUT_OPEN_ID,
    GATE2_INPUT_CLOSED_ID,
)
from controllers.base import BaseGateController


class QuidoGateController(BaseGateController):
    def __init__(self) -> None:
        self.quido_ip = QUIDO_IP
        self.base_url = f"http://{self.quido_ip}"

        self.gates = {
            1: {
                "output_open": GATE1_OUTPUT_OPEN_ID,
                "output_close": GATE1_OUTPUT_CLOSE_ID,
                "input_open": GATE1_INPUT_OPEN_ID,
                "input_closed": GATE1_INPUT_CLOSED_ID,
            },
            2: {
                "output_open": GATE2_OUTPUT_OPEN_ID,
                "output_close": GATE2_OUTPUT_CLOSE_ID,
                "input_open": GATE2_INPUT_OPEN_ID,
                "input_closed": GATE2_INPUT_CLOSED_ID,
            },
        }

    def _quido_get(self, path: str) -> str:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"Quido neodpovedá: {e}")

    def _pulse_output(self, output_id: int) -> None:
        self._quido_get(f"set.xml?type=s&id={output_id}")
        time.sleep(PULSE_SECONDS)
        self._quido_get(f"set.xml?type=r&id={output_id}")

    def _get_fresh_xml(self) -> str:
        return self._quido_get("fresh.xml")

    def _parse_inputs(self, root: ET.Element) -> dict[int, int]:
        inputs: dict[int, int] = {}

        for din in root.findall(".//din"):
            try:
                din_id = int(din.attrib.get("id", "0"))
                val = int(din.attrib.get("val", "0"))
                sts = int(din.attrib.get("sts", "0"))
            except ValueError:
                continue

            if sts == 0:
                inputs[din_id] = val

        return inputs

    def _parse_temperature(self, root: ET.Element) -> dict:
        for temp in root.findall(".//temp"):
            try:
                temp_id = int(temp.attrib.get("id", "0"))
                temp_sts = int(temp.attrib.get("sts", "1"))
                temp_val = float(temp.attrib.get("val", "0"))
            except ValueError:
                continue

            return {
                "id": temp_id,
                "value": temp_val,
                "valid": temp_sts == 0,
            }

        return {
            "id": None,
            "value": None,
            "valid": False,
        }

    def _parse_fresh_xml(self, xml_text: str) -> tuple[dict[int, int], dict]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            raise HTTPException(status_code=500, detail=f"Neplatné XML z Quido: {e}")

        inputs = self._parse_inputs(root)
        temperature = self._parse_temperature(root)
        return inputs, temperature

    def _derive_gate_state(self, gate_id: int, inputs: dict[int, int]) -> str:
        gate = self.gates[gate_id]
        input_open_id = gate["input_open"]
        input_closed_id = gate["input_closed"]

        if input_open_id is None or input_closed_id is None:
            return "unknown"

        if input_open_id not in inputs or input_closed_id not in inputs:
            return "unknown"

        input_open = inputs[input_open_id]
        input_closed = inputs[input_closed_id]

        if input_open == 1 and input_closed == 0:
            return "open"
        if input_open == 0 and input_closed == 1:
            return "closed"
        if input_open == 0 and input_closed == 0:
            return "moving"
        if input_open == 1 and input_closed == 1:
            return "error"

        return "unknown"

    def get_gate_status(self, gate_id: int) -> dict:
        if gate_id not in self.gates:
            raise HTTPException(status_code=404, detail="Neznáma závora")

        xml_text = self._get_fresh_xml()
        inputs, temperature = self._parse_fresh_xml(xml_text)
        state = self._derive_gate_state(gate_id, inputs)

        return {
            "gate_id": gate_id,
            "state": state,
            "last_action": None,
            "last_change": "",
            "is_busy": state == "moving",
            "detail": "Stav načítaný z Quido",
            "quido_ip": self.quido_ip,
            "inputs": inputs,
            "temperature": temperature,
        }

    def get_all_gates_status(self) -> dict:
        xml_text = self._get_fresh_xml()
        inputs, temperature = self._parse_fresh_xml(xml_text)

        gate_1 = {
            "gate_id": 1,
            "state": self._derive_gate_state(1, inputs),
            "last_action": None,
            "last_change": "",
            "is_busy": self._derive_gate_state(1, inputs) == "moving",
            "detail": "Stav načítaný z Quido",
            "quido_ip": self.quido_ip,
            "inputs": inputs,
            "temperature": temperature,
        }

        gate_2 = {
            "gate_id": 2,
            "state": self._derive_gate_state(2, inputs),
            "last_action": None,
            "last_change": "",
            "is_busy": self._derive_gate_state(2, inputs) == "moving",
            "detail": "Stav načítaný z Quido",
            "quido_ip": self.quido_ip,
            "inputs": inputs,
            "temperature": temperature,
        }

        return {
            "gate_1": gate_1,
            "gate_2": gate_2,
            "temperature": temperature,
        }

    def open_gate_by_id(self, gate_id: int) -> dict:
        if gate_id not in self.gates:
            raise HTTPException(status_code=404, detail="Neznáma závora")

        status = self.get_gate_status(gate_id)

        if status["state"] == "error":
            raise HTTPException(status_code=409, detail=f"Závora {gate_id} je v chybovom stave")

        if status["state"] == "open":
            return {
                "ok": True,
                "gate_id": gate_id,
                "action": "open",
                "state": "open",
                "detail": f"Závora {gate_id} je už otvorená",
            }

        self._pulse_output(self.gates[gate_id]["output_open"])

        return {
            "ok": True,
            "gate_id": gate_id,
            "action": "open",
            "state": "moving",
            "detail": f"Odoslaný OPEN pulz pre závoru {gate_id}",
        }

    def close_gate_by_id(self, gate_id: int) -> dict:
        if gate_id not in self.gates:
            raise HTTPException(status_code=404, detail="Neznáma závora")

        status = self.get_gate_status(gate_id)

        if status["state"] == "error":
            raise HTTPException(status_code=409, detail=f"Závora {gate_id} je v chybovom stave")

        if status["state"] == "closed":
            return {
                "ok": True,
                "gate_id": gate_id,
                "action": "close",
                "state": "closed",
                "detail": f"Závora {gate_id} je už zatvorená",
            }

        self._pulse_output(self.gates[gate_id]["output_close"])

        return {
            "ok": True,
            "gate_id": gate_id,
            "action": "close",
            "state": "moving",
            "detail": f"Odoslaný CLOSE pulz pre závoru {gate_id}",
        }

    def get_status(self) -> dict:
        return self.get_gate_status(1)

    def open_gate(self) -> dict:
        return self.open_gate_by_id(1)

    def close_gate(self) -> dict:
        return self.close_gate_by_id(1)

    def reset_gate(self) -> dict:
        return {"ok": True, "detail": "Reset nie je implementovaný pre Quido"}

    def fault_gate(self) -> dict:
        return {"ok": True, "detail": "Fault simulácia nie je implementovaná pre Quido"}

    def offline_gate(self) -> dict:
        return {"ok": True, "detail": "Offline simulácia nie je implementovaná pre Quido"}