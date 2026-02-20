import { useEffect, useState } from "react";
import { Card, Row, Col, Alert, Button, Form, Badge } from "react-bootstrap";
import { api } from "../api";

export default function WorkoutViewer() {
  const [sessions, setSessions] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [sessionData, setSessionData] = useState(null);

  const [statusMsg, setStatusMsg] = useState({ type: "", text: "" });
  const [err, setErr] = useState("");

  const [date, setDate] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [location, setLocation] = useState("");
  const [notes, setNotes] = useState("");
  const [visibility, setVisibility] = useState("friends");

  const [setEdits, setSetEdits] = useState({});

  useEffect(() => {
    api("/viewer/sessions")
      .then((resp) => {
        if (resp && Array.isArray(resp.items)) setSessions(resp.items);
        else setSessions([]);
      })
      .catch((e) => {
        console.error(e);
        setErr("Could not load sessions.");
      });
  }, []);

  function findSelectedMeta() {
    for (let i = 0; i < sessions.length; i++) {
      if (String(sessions[i].id) === String(selectedId)) return sessions[i];
    }
    return null;
  }

  const selectedMeta = findSelectedMeta();
  const isFuture = selectedMeta ? !!selectedMeta.is_future : false;

  async function loadSession(id) {
    setErr("");
    setStatusMsg({ type: "", text: "" });
    setSessionData(null);
    setSetEdits({});

    try {
      const resp = await api(`/viewer/sessions/${id}`);
      const s = resp ? resp.session : null;
      if (!s) throw new Error("No session returned");

      setSessionData(s);

      setDate(s.date || "");
      setStartTime(s.start_time || "");
      setEndTime(s.end_time || "");
      setLocation(s.location || "");
      setNotes(s.notes || "");
      setVisibility(s.visibility ? "friends" : "private");

      const edits = {};
      const items = Array.isArray(s.items) ? s.items : [];
      for (let i = 0; i < items.length; i++) {
        const it = items[i];
        const key = `${it.exercise_id}-${it.set_number}`;
        edits[key] = {
          weight: it.weight == null ? "" : String(it.weight),
          reps: it.reps == null ? "" : String(it.reps),
        };
      }
      setSetEdits(edits);
    } catch (e) {
      console.error(e);
      setErr("Failed to load session details.");
    }
  }

  function handleSelectChange(e) {
    const id = e.target.value;
    setSelectedId(id);
    if (id) loadSession(id);
  }

  async function saveSessionDetails() {
    if (!selectedId) return;

    try {
      const visBit = visibility === "friends" ? 1 : 0;

      await api(`/viewer/sessions/${selectedId}`, {
        method: "PUT",
        body: JSON.stringify({
          date: date,
          start_time: startTime,
          end_time: endTime,
          location: location,
          notes: notes,
          visibility: visBit,
        }),
      });

      setStatusMsg({ type: "success", text: "Session details updated." });
      const refreshed = await api("/viewer/sessions");
      if (refreshed && Array.isArray(refreshed.items)) setSessions(refreshed.items);

      // reloads this session
      await loadSession(selectedId);
    } catch (e) {
      console.error(e);
      setStatusMsg({ type: "danger", text: "Failed to update session details." });
    }
  }

  function groupExercises(items) {
    // returns array with info we need
    const groups = {};

    for (let i = 0; i < items.length; i++) {
      const it = items[i];
      const exId = it.exercise_id;

      if (!groups[exId]) {
        groups[exId] = {
          exercise_id: exId,
          name: it.name,
          category: it.category,
          is_pr: it.is_pr,
          sets: [],
        };
      }

      groups[exId].sets.push({
        set_number: it.set_number,
        weight: it.weight,
        reps: it.reps,
      });
    }

    const arr = [];
    for (const k in groups) arr.push(groups[k]);

    for (let i = 0; i < arr.length; i++) {
      for (let j = i + 1; j < arr.length; j++) {
        if ((arr[j].name || "") < (arr[i].name || "")) {
          const tmp = arr[i];
          arr[i] = arr[j];
          arr[j] = tmp;
        }
      }
    }

    for (let i = 0; i < arr.length; i++) {
      const sets = arr[i].sets;
      for (let a = 0; a < sets.length; a++) {
        for (let b = a + 1; b < sets.length; b++) {
          if (sets[b].set_number < sets[a].set_number) {
            const tmp2 = sets[a];
            sets[a] = sets[b];
            sets[b] = tmp2;
          }
        }
      }
    }

    return arr;
  }

  async function saveOneSet(exerciseId, setNumber) {
    if (!selectedId) return;

    const key = `${exerciseId}-${setNumber}`;
    const cur = setEdits[key] || { weight: "", reps: "" };

    try {
      await api("/viewer/exercise", {
        method: "PUT",
        body: JSON.stringify({
          session_id: Number(selectedId),
          exercise_id: Number(exerciseId),
          set_number: Number(setNumber),
          weight: cur.weight === "" ? null : Number(cur.weight),
          reps: cur.reps === "" ? null : Number(cur.reps),
        }),
      });

      setStatusMsg({ type: "success", text: `Updated set ${setNumber}.` });
      await loadSession(selectedId);
    } catch (e) {
      console.error(e);
      setStatusMsg({ type: "danger", text: "Failed to update set." });
    }
  }

  let grouped = [];
  if (sessionData && Array.isArray(sessionData.items)) {
    grouped = groupExercises(sessionData.items);
  }

  return (
    <div className="py-3">
      <h1 className="mb-1">Workout Viewer</h1>
      <p className="text-muted small mb-3">
        Select a session and edit its details. Past sessions also allow editing exercise sets.
      </p>

      {statusMsg.text && (
        <Alert
          variant={statusMsg.type}
          onClose={() => setStatusMsg({ type: "", text: "" })}
          dismissible
        >
          {statusMsg.text}
        </Alert>
      )}

      {err && <Alert variant="danger">{err}</Alert>}

      {/* Dropdown */}
      <Card className="shadow-sm mb-3">
        <Card.Body>
          <Form.Label className="fw-semibold">Choose a session</Form.Label>
          <Form.Select value={selectedId} onChange={handleSelectChange}>
            <option value="">-- Select a session --</option>
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.date} · {s.start_time}-{s.end_time} · {s.location || "No location"}{" "}
                {s.is_future ? "(future)" : "(past)"}
              </option>
            ))}
          </Form.Select>
        </Card.Body>
      </Card>

      {!selectedId && <Alert variant="secondary">Pick a session to begin.</Alert>}

      {selectedId && (
        <>
          {/* Session details */}
          <Card className="shadow-sm mb-3">
            <Card.Body>
              <div className="d-flex justify-content-between align-items-center mb-2">
                <h5 className="mb-0">Session details</h5>
                {isFuture ? (
                  <Badge bg="warning" text="dark">Future</Badge>
                ) : (
                  <Badge bg="success">Past</Badge>
                )}
              </div>

              <Row className="g-3">
                <Col md={3}>
                  <Form.Label>Date</Form.Label>
                  <Form.Control type="date" value={date} onChange={(e) => setDate(e.target.value)} />
                </Col>
                <Col md={3}>
                  <Form.Label>Start</Form.Label>
                  <Form.Control type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
                </Col>
                <Col md={3}>
                  <Form.Label>End</Form.Label>
                  <Form.Control type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
                </Col>
                <Col md={3}>
                  <Form.Label>Visibility</Form.Label>
                  <Form.Select value={visibility} onChange={(e) => setVisibility(e.target.value)}>
                    <option value="friends">Friends</option>
                    <option value="private">Private</option>
                  </Form.Select>
                </Col>

                <Col md={6}>
                  <Form.Label>Location</Form.Label>
                  <Form.Control value={location} onChange={(e) => setLocation(e.target.value)} />
                </Col>
                <Col md={6}>
                  <Form.Label>Notes</Form.Label>
                  <Form.Control value={notes} onChange={(e) => setNotes(e.target.value)} />
                </Col>
              </Row>

              <div className="mt-3">
                <Button variant="primary" onClick={saveSessionDetails}>
                  Save session details
                </Button>
              </div>
            </Card.Body>
          </Card>

          {/* Exercises */}
          <Card className="shadow-sm">
            <Card.Body style={isFuture ? { opacity: 0.5 } : {}}>
              <div className="d-flex justify-content-between align-items-center mb-2">
                <h5 className="mb-0">Exercises</h5>
                {isFuture && <span className="text-muted small">Disabled for future sessions</span>}
              </div>

              {grouped.length === 0 && (
                <Alert variant="secondary" className="mb-0">
                  No exercises logged for this session.
                </Alert>
              )}

              {grouped.map((ex) => (
                <Card key={ex.exercise_id} className="mb-3">
                  <Card.Body>
                    <div className="d-flex justify-content-between align-items-start">
                      <div>
                        <div className="fw-semibold">{ex.name}</div>
                        <div className="text-muted small">{ex.category}</div>
                      </div>
                      {ex.is_pr ? <Badge bg="info">PR</Badge> : null}
                    </div>

                    <div className="mt-3">
                      {ex.sets.map((st) => {
                        const key = `${ex.exercise_id}-${st.set_number}`;
                        const cur = setEdits[key] || { weight: "", reps: "" };

                        return (
                          <Row key={key} className="align-items-end g-2 mb-2">
                            <Col md={2}>
                              <div className="small text-muted">Set</div>
                              <Form.Control value={st.set_number} disabled />
                            </Col>
                            <Col md={4}>
                              <div className="small text-muted">Weight</div>
                              <Form.Control
                                type="number"
                                step="0.5"
                                value={cur.weight}
                                disabled={isFuture}
                                onChange={(e) => {
                                  const newVal = e.target.value;
                                  setSetEdits((prev) => {
                                    const copy = { ...prev };
                                    const existing = copy[key] || { weight: "", reps: "" };
                                    copy[key] = { weight: newVal, reps: existing.reps };
                                    return copy;
                                  });
                                }}
                              />
                            </Col>
                            <Col md={4}>
                              <div className="small text-muted">Reps</div>
                              <Form.Control
                                type="number"
                                value={cur.reps}
                                disabled={isFuture}
                                onChange={(e) => {
                                  const newVal = e.target.value;
                                  setSetEdits((prev) => {
                                    const copy = { ...prev };
                                    const existing = copy[key] || { weight: "", reps: "" };
                                    copy[key] = { weight: existing.weight, reps: newVal };
                                    return copy;
                                  });
                                }}
                              />
                            </Col>
                            <Col md={2}>
                              <Button
                                variant="outline-primary"
                                className="w-100"
                                disabled={isFuture}
                                onClick={() => saveOneSet(ex.exercise_id, st.set_number)}
                              >
                                Save
                              </Button>
                            </Col>
                          </Row>
                        );
                      })}
                    </div>
                  </Card.Body>
                </Card>
              ))}
            </Card.Body>
          </Card>
        </>
      )}
    </div>
  );
}