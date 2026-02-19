import { useEffect, useMemo, useState } from "react";
import { Row, Col, Card, Form, Button, Table, Alert, Badge } from "react-bootstrap";
import { api } from "../api";

// src/pages/Workouts.jsx
export default function Workouts() {

  // Here I am storing the form data
  const [exercises, setExercises] = useState([]);

  // Here I am storing the Form state
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [duration, setDuration] = useState(30);
  const [rows, setRows] = useState([{ name: "", category: "strength", weight_kg: "", reps: "", sets: "" }]);
  const [notes, setNotes] = useState("")

  // Storing information about the state of the user interface itself
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [prs, setPrs] = useState([]);

  const [validated, setValidated] = useState(false);

  const [scheduleSlots, setScheduleSlots] = useState([]);
  const [selectedSlotId, setSelectedSlotId] = useState("");

  // Here I am loading the set of exercises which are registered, and if none are registered then I am just passing an empty list
  useEffect(() => {
    api("/exercises")
    .then((resp) => setExercises(Array.isArray(resp?.items) ? resp.items : []))
    .catch((e) => {
      console.log("EXERCISES ERROR =", e);
      setExercises([]);
    });
    
    api("/schedule/slots")
      .then((resp) => setScheduleSlots(Array.isArray(resp?.items) ? resp.items : []))
      .catch(() => setScheduleSlots([]));

    
  }, []);

  

  // These are helper functions which I created for dynamically updating rows
  // I learnt that in React one cannot directly mutate/edit the variable/state so they have to create a copy and then use the setter to assign it to the new updated object

  function setRow(i, patch) {
    setRows((oldRows) => {
      // This part creates a copy of the Old Rows array
      const newRows = [...oldRows];

      // This part looks at the row specified by i, and the specific entry specified by patch and updates/overwrites the old entry/row with the new one.
      newRows[i] = {
        ...newRows[i],
        ...patch,
      };
      return newRows;
    });
  }

  function addRow() {
    setRows((oldRows) => {
      const newRow = { name: "", category: "strength", weight_kg: "", reps: "", sets: "" };
      // This is a clean way of copying old array to a new one and adding the new row to
      return [...oldRows, newRow];
    });
  }

  function removeRow(i) {
    setRows((oldRows) => {
      // The filter function creates a new array that contains only the elements where the funciton or the callback returns true
      // The (_, idx) looks at the value, index of each entry and makes the comparison of index with the passed in index/argument
      // For every entry which doesn't have the index requested, it is added to the newRows array but the one we wish to remove is not
      const newRows = oldRows.filter((_, idx) => idx !== i);
      return newRows;
    });
  }

  // Here I am doing client side validation of the Form
  // Again, this part uses the useMemo function which is react's way of caching data
  const canSubmit = useMemo(() => {
    if (!date) {
      return false;
    }
    if (Number.isNaN(+duration) || +duration <= 0) {
      return false;
    }
    if (rows.length === 0) {
      return false;
    }

    // Doing verification checks on validity of data retrieved
    // Note, that I found this out online that a + infront of a number based string is easiers/fastest way of converting it to a number/int
    for (const r of rows) {
      if (!r.name) return false;
      if (!r.reps || +r.reps < 1) return false;
      if (!r.sets || +r.sets < 1) return false;
      if (r.weight_kg === "" || +r.weight_kg < 0) return false;
    }
    return true;
  }, [date, duration, rows]);

  function getValidationError() {
    if (!selectedSlotId) return "Please select a schedule slot first.";
    if (!date) return "Please select a workout date.";
    const selectedDate = new Date(date);
    const today = new Date();
    today.setHours(23, 59, 59, 999);
    if (selectedDate > today) return "Workout date cannot be in the future.";
    if (Number.isNaN(+duration) || +duration <= 0) return "Duration must be a positive number of minutes.";
    if (+duration > 600) return "Duration cannot exceed 600 minutes (10 hours).";
    if (rows.length === 0) return "Add at least one exercise to your workout.";

    for (let i = 0; i < rows.length; i++) {
      const r = rows[i];
      const label = `Exercise row ${i + 1}`;
      if (!r.name) return `${label}: Please select an exercise.`;
      if (!r.reps || +r.reps < 1) return `${label}: Reps must be at least 1.`;
      if (+r.reps > 100) return `${label}: Reps cannot exceed 100 per set.`;
      if (!r.sets || +r.sets < 1) return `${label}: Sets must be at least 1.`;
      if (+r.sets > 50) return `${label}: Sets cannot exceed 50.`;
      if (r.weight_kg === "" || +r.weight_kg < 0) return `${label}: Weight must be 0 or more.`;
      if (+r.weight_kg > 1000) return `${label}: Weight cannot exceed 1000 kg.`;
    }
    return "";
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setInfo("");
    setPrs([]);
    setValidated(true);

    const validationMsg = getValidationError();
    if (validationMsg) {
      setError(validationMsg);
      return;
    }

    setSaving(true);
    try {

      // Here I am simply defining the payload that will be sent as part of the api call to workouts page
      const workoutPayload = {
        session_id: selectedSlotId ? Number(selectedSlotId) : null,
        date,
        duration_minutes: Number(duration),
        notes: notes.trim(),
        items: rows.map((row) => ({
          name: row.name,
          category: row.category || "strength",
          weight_kg: Number(row.weight_kg),
          reps: Number(row.reps),
          sets: Number(row.sets),
          session_id: selectedSlotId ? Number(selectedSlotId) : null,
        }))

      };

      // Single request – backend handles creating workout + items + PRs
      const created = await api("/workouts", {
        method: "POST",
        body: workoutPayload,
      });

      // PRs come back in created.result.new_prs (per your Flask route)
      const prs = created?.result?.new_prs;
      if (Array.isArray(prs)) {
        setPrs(prs);
      }

      setInfo("Workout has been saved! Nice job 💪.");

      // Reset the form
      setRows([{ name: "", category: "strength", weight_kg: "", reps: "", sets: "" }]);
      setNotes("");
      setValidated(false);
    } catch (err) {
      setError(err.message || "Failed to save the workout.");
    } finally {
      setSaving(false);
    }
  }

  function exerciseNameById(id) {
    const exercise = exercises.find((exercise) => exercise.id === id);
    return exercise ? exercise.name : `#${id}`;
  }

  return (
    <div className="workouts-page py-3">
      <h1 className="mb-3">Log a workout</h1>

      <Row>
        {/* This is the main part of the form, positioned towards the left of the screen */}
        <Col lg={7} className="mb-4">
          <Card className="workout-form-card shadow-sm">
            <Card.Body>
              <Form onSubmit={handleSubmit}>
                <Row className="mb-3">
                  <Col md={6}>
                    <Form.Group controlId="workoutDate" className="mb-3 mb-md-0">
                      <Form.Label>Date</Form.Label>
                      <Form.Control
                        type="date"
                        value={date}
                        onChange={(e) => setDate(e.target.value)}
                        isInvalid={validated && !date}
                      />
                      <Form.Control.Feedback type="invalid">
                        Please select a date.
                      </Form.Control.Feedback>
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group controlId="durationMinutes">
                      <Form.Label>Duration (minutes)</Form.Label>
                      <Form.Control
                        type="number"
                        min={1}
                        max={600}
                        value={duration}
                        onChange={(e) => setDuration(e.target.value)}
                        isInvalid={validated && (Number.isNaN(+duration) || +duration <= 0 || +duration > 600)}
                      />
                      <Form.Control.Feedback type="invalid">
                        Duration must be between 1 and 600 minutes.
                      </Form.Control.Feedback>
                    </Form.Group>
                  </Col>
                </Row>

                <h5 className="mt-2 mb-2">Exercises</h5>
                <p className="text-muted small mb-2">
                  Reps are <strong>per set</strong>. Total reps = sets x reps.
                </p>

                <div className="table-responsive mb-3">
                  <Table size="sm" className="align-middle">
                    <thead>
                      <tr>
                        <th style={{ width: "30%" }}>Exercise</th>
                        <th style={{ width: "15%" }}>Weight (kg)</th>
                        <th style={{ width: "15%" }}>Reps / set</th>
                        <th style={{ width: "15%" }}>Sets</th>
                        <th style={{ width: "15%" }}>Total Reps</th>
                        <th style={{ width: "15%" }} />
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((r, idx) => {
                        const totalReps = (Number(r.reps) || 0) * (Number(r.sets) || 0);
                        return (
                          <tr key={idx}>
                            <td>
                              <div className="small text-muted mb-2">
                                Exercises loaded: {exercises.length}
                              </div>
                              <Form.Select
                                value={r.name}
                                onChange={(e) => {
                                  const selectedName = e.target.value;
                                  const ex = exercises.find((x) => x.name === selectedName);
                                  setRow(idx, { name: selectedName, category: ex?.category || "strength" });
                                }}
                                isInvalid={validated && !r.name}
                              >
                                <option value="">Select...</option>
                                {exercises.map((ex) => (
                                  <option key={ex.id} value={ex.name}>
                                    {ex.name}
                                  </option>
                                ))}
                              </Form.Select>
                            </td>
                            <td>
                              <Form.Control
                                type="number"
                                min={0}
                                max={1000}
                                step="0.5"
                                value={r.weight_kg}
                                onChange={(e) => setRow(idx, { weight_kg: e.target.value })}
                                isInvalid={validated && (r.weight_kg === "" || +r.weight_kg < 0 || +r.weight_kg > 1000)}
                              />
                            </td>
                            <td>
                              <Form.Control
                                type="number"
                                min={1}
                                max={100}
                                value={r.reps}
                                onChange={(e) => setRow(idx, { reps: e.target.value })}
                                isInvalid={validated && (!r.reps || +r.reps < 1 || +r.reps > 100)}
                              />
                            </td>
                            <td>
                              <Form.Control
                                type="number"
                                min={1}
                                max={50}
                                value={r.sets}
                                onChange={(e) => setRow(idx, { sets: e.target.value })}
                                isInvalid={validated && (!r.sets || +r.sets < 1 || +r.sets > 50)}
                              />
                            </td>
                            <td>
                              <span className="small text-mutated">
                                {totalReps || "-"}
                              </span>
                            </td>
                            <td className="exercise-row-actions text-end">
                              {rows.length > 1 && (
                                <Button variant="outline-danger" size="sm" onClick={() => removeRow(idx)} >x</Button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </Table>
                </div>

                <Button variant="outline-maroon" size="sm" className="mb-3" type="button" onClick={addRow} >+ Add exercise row</Button>

                <Form.Group className="mb-3" controlId="notes">
                  <Form.Label>Notes</Form.Label>
                  <Form.Control as="textarea" rows={3} placeholder="How did the workout feel? Any PR attempts? Etc." value={notes} onChange={(e) => setNotes(e.target.value)} />
                </Form.Group>

                {error && (<Alert variant="danger" className="py-2">{error}</Alert>)}
                {info && (<Alert variant="success" className="py-2">{info}</Alert>)}

                {prs.length > 0 && (
                  <Alert variant="info" className="py-2 mt-2">
                    <strong>New PRs!</strong>
                    {prs.map((pr, i) => (
                      <span key={pr.id || i}>
                        {i > 0 ? ", " : ""}
                        {exerciseNameById(pr.exercise_id)} —{" "}
                        {pr.best_weight_kg} kg x {pr.best_reps}{" "}
                        <Badge bg="light" text="dark">est. {pr.best_1rm_kg.toFixed(1)} kg 1RM</Badge>
                      </span>
                    ))}
                  </Alert>
                )}

                <div className="d-flex justify-content-end mt-3">
                  <Button type="submit" variant="maroon" disabled={!canSubmit || saving || !selectedSlotId}>
                    {saving ? "Saving workout..." : "Save workout"}
                  </Button>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </Col>

        <Col lg={5}>
          <Card className="workout-side-card shadow-sm mb-3">
            <Card.Body>
              <Card.Title as="h5" className="mb-3">
                Log workout for a schedule slot
              </Card.Title>

              <Form.Group controlId="slotSelect" className="mb-3">
                <Form.Label>Pick a slot</Form.Label>
                <Form.Select
                  value={selectedSlotId}
                  onChange={(e) => setSelectedSlotId(e.target.value)}
                >
                  <option value="">Select a slot...</option>
                  {scheduleSlots.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.date} · {s.start_time}-{s.end_time} · {s.location}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>

              {!selectedSlotId && (
                <Alert variant="warning" className="py-2 small mb-0">
                  You must select a slot before saving a workout.
                </Alert>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
}