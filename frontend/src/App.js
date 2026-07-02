import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE = "";
const API_KEY = "88083582";

const IDLE_POLL_MS = 15000;
const MOVING_POLL_MS = 1000;

function App() {
  const [gates, setGates] = useState({});
  const [initialLoading, setInitialLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState({});
  const [message, setMessage] = useState("");

  const timerRef = useRef(null);

  const stopPolling = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  const getFastestPollInterval = (data) => {
    const gate1 = data?.gate_1?.state;
    const gate2 = data?.gate_2?.state;

    if (gate1 === "moving" || gate2 === "moving") {
      return MOVING_POLL_MS;
    }
    return IDLE_POLL_MS;
  };

  const scheduleNextPoll = (data) => {
    stopPolling();
    const interval = getFastestPollInterval(data);

    timerRef.current = setTimeout(() => {
      fetchGates(false);
    }, interval);
  };

  const fetchGates = async (showInitialLoader = false) => {
    try {
      if (showInitialLoader) {
        setInitialLoading(true);
      }

      const response = await fetch(`${API_BASE}/api/gates`);
      const data = await response.json();

      setGates((prev) => {
        const prevJson = JSON.stringify(prev);
        const newJson = JSON.stringify(data);
        return prevJson === newJson ? prev : data;
      });

      scheduleNextPoll(data);
    } catch (error) {
      setMessage("Nepodarilo sa načítať stav závor.");
      scheduleNextPoll({});
    } finally {
      if (showInitialLoader) {
        setInitialLoading(false);
      }
    }
  };

  const sendAction = async (gateId, action) => {
    try {
      setActionLoading((prev) => ({ ...prev, [gateId]: true }));
      setMessage("");

      const response = await fetch(`${API_BASE}/api/gates/${gateId}/${action}`, {
        method: "POST",
        headers: {
          "X-API-Key": API_KEY,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        setMessage(data.detail || "Nastala chyba.");
        return;
      }

      setMessage(data.detail || `Akcia ${action} pre závoru ${gateId} odoslaná.`);
      await fetchGates(false);
    } catch (error) {
      setMessage("Nepodarilo sa odoslať príkaz.");
    } finally {
      setActionLoading((prev) => ({ ...prev, [gateId]: false }));
    }
  };

  useEffect(() => {
    fetchGates(true);

    return () => {
      stopPolling();
    };
  }, []);

  const getStateLabel = (state) => {
    switch (state) {
      case "open":
        return "Otvorená";
      case "closed":
        return "Zatvorená";
      case "moving":
        return "V pohybe";
      case "error":
        return "Chyba";
      case "offline":
        return "Offline";
      default:
        return "Neznámy stav";
    }
  };

  const renderGateCard = (gateId, gateData, title) => {
    return (
      <div className="card gateCard">
        <h2>{title}</h2>

        <div className="statusBox">
          <div className="statusTitle">Aktuálny stav</div>
          <div className="statusValue">
            {initialLoading
              ? "Načítavam..."
              : gateData
              ? getStateLabel(gateData.state)
              : "Bez dát"}
          </div>

          {gateData && (
            <div className="statusMeta">
              Posledná akcia: {gateData.last_action || "žiadna"}
              <br />
              Busy: {gateData.is_busy ? "áno" : "nie"}
              <br />
              IP Quido: {gateData.quido_ip || "-"}
            </div>
          )}
        </div>

        <div className="buttons">
          <button
            className="openBtn"
            onClick={() => sendAction(gateId, "open")}
            disabled={!!actionLoading[gateId]}
          >
            Otvoriť
          </button>

          <button
            className="closeBtn"
            onClick={() => sendAction(gateId, "close")}
            disabled={!!actionLoading[gateId]}
          >
            Zavrieť
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="app">
      <div className="container">
        <h1>Ovládanie závor</h1>

        <div className="topInfo">
          <div className="tempCard">
            <div className="tempTitle">Teplota</div>
            <div className="tempValue">
              {gates.temperature?.valid && gates.temperature?.value !== null
                ? `${gates.temperature.value} °C`
                : "Bez dát"}
            </div>
          </div>
        </div>

        <div className="grid">
          {renderGateCard(1, gates.gate_1, "Závora 1")}
          {renderGateCard(2, gates.gate_2, "Závora 2")}
        </div>

        <div className="actions globalActions">
          <button onClick={() => fetchGates(false)}>
            Obnoviť stav všetkých závor
          </button>
        </div>

        {message && <div className="message">{message}</div>}
      </div>
    </div>
  );
}

export default App;