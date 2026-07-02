from config import MODE
from controllers.mock_controller import MockGateController
from controllers.quido_controller import QuidoGateController


class GateService:
    def __init__(self) -> None:
        if MODE == "mock":
            self.controller = MockGateController()
        elif MODE == "quido":
            self.controller = QuidoGateController()
        else:
            raise ValueError(f"Neznámy MODE: {MODE}")

    def get_status(self) -> dict:
        return self.controller.get_status()

    def open_gate(self) -> dict:
        return self.controller.open_gate()

    def close_gate(self) -> dict:
        return self.controller.close_gate()

    def reset_gate(self) -> dict:
        return self.controller.reset_gate()

    def fault_gate(self) -> dict:
        return self.controller.fault_gate()

    def offline_gate(self) -> dict:
        return self.controller.offline_gate()

    def get_gate_status(self, gate_id: int) -> dict:
        return self.controller.get_gate_status(gate_id)

    def get_all_gates_status(self) -> dict:
        return self.controller.get_all_gates_status()

    def open_gate_by_id(self, gate_id: int) -> dict:
        return self.controller.open_gate_by_id(gate_id)

    def close_gate_by_id(self, gate_id: int) -> dict:
        return self.controller.close_gate_by_id(gate_id)