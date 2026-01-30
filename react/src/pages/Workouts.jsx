import { useEffect, useMemo, useState } from "react";
import { Row, Col, Card, Form, Button, Table, Alert, Badge } from "react-bootstrap";
import { api } from "../api";

// src/pages/Workouts.jsx
export default function Workouts() {

  // Here I am storing the form data
  const [exercises, setExercises] = useState([]);
  const [recent, setRecent] = useState([]);

  // Here I am storing the Form state
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [duration, setDuration] = useState(30);
  const [rows, setRows] = useState([{ exercise_id: "", weight_kg: "", reps: "", sets: "" }]);
  const [notes, setNotes] = useState("")

  // Storing information about the state of the user interface itself
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [prs, setPrs] = useState([]);

  // Here I am loading the set of exercises which are registered, and if none are registered then I am just passing an empty list
  useEffect(() => {
    api("/exercises")
      .then((resp) => setExercises(resp || []))
      .catch(() => setExercises([]));
    
    refreshRecent();
  }, []);

  function refreshRecent() {
    api("/workouts")
      .then((resp) => {
        const items = Array.isArray(resp?.items) ? resp.items : [];
        console.log("Workouts recent resp:", resp);    
        setRecent(items);
      })
      .catch(() => setRecent([]));
  }

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
      const newRow = { exercise_id: "", weight_kg: "", reps: "", sets: "" };
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
      if (!r.exercise_id) return false;
      if (!r.reps || +r.reps < 1) return false;
      if (!r.sets || +r.sets < 1) return false;
      if (r.weight_kg === "" || +r.weight_kg < 0) return false;
    }
    return true;
  }, [date, duration, rows]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setInfo("");
    setPrs([]);

    if (!canSubmit) {
      setError("One or more of the workout fields is filled incorrectly.");
      return;
    }

    setSaving(true);
    try {

      // Here I am simply defining the payload that will be sent as part of the api call to workouts page
      const workoutPayload = {
        date,
        duration_minutes: Number(duration),
        notes: notes.trim(),
        items: rows.map((row) => ({
          exercise_id: Number(row.exercise_id),
          weight_kg: Number(row.weight_kg),
          reps: Number(row.reps),
          sets: Number(row.sets),
        })),
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
      setRows([{ exercise_id: "", weight_kg: "", reps: "", sets: "" }]);
      setNotes("");
      refreshRecent();
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
                      <Form.Control type="date" value={date} onChange={(e) => setDate(e.target.value)} />
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group controlId="durationMinutes">
                      <Form.Label>Duration (minutes)</Form.Label>
                      <Form.Control type="number" min={1} value={duration} onChange={(e) => setDuration(e.target.value)} />
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
                              <Form.Select value={r.exercise_id} onChange={(e) => setRow(idx, { exercise_id: e.target.value })} >
                                <option value="">Select...</option>
                                {exercises.map((ex) => (
                                  <option key={ex.id} value={ex.id}>{ex.name}</option>
                                ))}
                              </Form.Select>
                            </td>
                            <td>
                              <Form.Control type="number" min={0} step="0.5" value={r.weight_kg} onChange={(e) => setRow(idx, { weight_kg: e.target.value })} />
                            </td>
                            <td>
                              <Form.Control type="number" min={1} value={r.reps} onChange={(e) => setRow(idx, { reps: e.target.value })} />
                            </td>
                                                        <td>
                              <Form.Control type="number" min={1} value={r.sets} onChange={(e) => setRow(idx, { sets: e.target.value })} />
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
                  <Button type="submit" variant="maroon" disabled={!canSubmit || saving} >
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
                Recent workouts
              </Card.Title>
              {recent.length === 0 && (
                <p className="text-muted small mb-0">
                  No workouts logged yet. Your last few sessions will show up
                  here once you start using ShreddedNerds.
                </p>
              )}
              {recent.slice(0, 5).map((w) => {
                const dateStr = w.date || w.day;
                return (
                  <div
                    key={w.id}
                    className="d-flex justify-content-between small mb-2"
                  >
                    <div>
                      <div className="fw-semibold">{dateStr}</div>
                      <div className="text-muted">
                        {w.duration_minutes} min
                        {w.notes ? ` · ${w.notes.slice(0, 40)}…` : ""}
                      </div>
                    </div>
                    <div className="text-end text-muted">
                      <div>ID #{w.id}</div>
                    </div>
                  </div>
                );
              })}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
