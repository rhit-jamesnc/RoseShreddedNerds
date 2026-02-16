import { useState, useEffect } from "react";
import { Card, Row, Col, Form, Button, Badge } from "react-bootstrap";
import { api } from "../api";

export default function Schedule() {

  // These are variables/trackers which store the state of the UI or about the UI
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  // These are the actual variables where I am storing information about the creation of the schedule slot itself
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [startTime, setStartTime] = useState("17:00");
  const [endTime, setEndTime] = useState("18:00");
  const [location, setLocation] = useState("SRC main weight room");
  const [note, setNote] = useState("");
  const [visibility, setVisibility] = useState("friends");
  const [saving, setSaving] = useState(false);
  const [info, setInfo] = useState("");


  useEffect(() => {
    refreshSlots();
  }, []);

  // Helper function to load the schedules
  function refreshSlots() {
    setLoading(true);
    setErr("");
    api("/schedule/slots")
      .then((resp) => {
        const items = Array.isArray(resp?.items) ? [...resp.items] : [];
        items.sort((a, b) => (a.start_time || "").localeCompare(b.start_time || ""));
        setSlots(items);
      })
      .catch((e) => {
        console.error(e);
        setErr("Could not load your schedule.");
        setSlots([]);
      })
      .finally(() => setLoading(false));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setErr("");
    setInfo("");

    // Simple validation to make sure all the fields have a value being entered into them
    if (!date || !startTime || !endTime || !location.trim()) {
      setErr("Please fill in date, time, and location");
      return;
    }

    // Basic validation to ensure that start and end date are a valid combination
    const startStr = `${date} ${startTime}`;
    const endStr = `${date} ${endTime}`;
    if (endStr <= startStr) {
      setErr("End time must be after start time");
      return;
    }

    // Here I am just creating the payload that will be send as part of the post request
    const payload = {
      date: date,
      start_time: startTime, 
      end_time: endTime,      
      location: location.trim(),
      note: note.trim(),
      visibility,
    };


    setSaving(true);
    try {
      await api("/schedule/slots", {
        method: "POST",
        body: payload,
      });
      setInfo("Added to your gym schedule");
      setNote("");
      refreshSlots();
    } catch (e) {
      console.error(e);
      setErr(e.message || "Could not save the schedule slot");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="schedule-page py-3">
      <div className="d-flex justify-content-between align-items-baseline mb-3">
        <div>
          <h1 className="mb-1">My Gym Schedule</h1>
          <p className="text-muted mb-0 small">
            Save when you plan to hit the SRC. Later, friends can see when you&apos;re training.
          </p>
        </div>
      </div>

      <Row>
        {/* This card on the left of the screen lists all the schedule slots created/upcoming workout sessions */}
        <Col md={7} className="mb-3">
          <Card className="schedule-card shadow-sm">
            <Card.Body>
              <Card.Title as="h5" className="mb-2">Upcoming slots</Card.Title>

              {loading && (<p className="small text-muted mb-0">Loading your schedule…</p>)}

              {!loading && slots.length === 0 && !err && (
                <p className="small text-muted mb-0">
                  You haven't added any gym times yet. Use the form on the right to
                  create your first slot.
                </p>
              )}

              {err && (<p className="small text-danger mb-2">{err}</p>)}

              {!loading && slots.length > 0 && (
                <div>
                  {slots.map((slot) => (
                    <div
                      key={slot.id}
                      className="schedule-slot-row d-flex justify-content-between small"
                    >
                      <div>
                        <div className="fw-semibold">
                          {slot.date} • {slot.start_time} → {slot.end_time}
                        </div>
                        <div className="text-muted">
                          {slot.location}
                          {slot.note ? ` · ${slot.note}` : ""}
                        </div>
                      </div>
                      <div className="text-end">
                        <Badge
                          bg="light"
                          text="dark"
                          className="border mb-1"
                        >
                          {slot.visibility || "friends"}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>

        {/* RIGHT: add form */}
        <Col md={5}>
          <Card className="schedule-card shadow-sm">
            <Card.Body>
              <Card.Title as="h5" className="mb-2">
                Add gym time
              </Card.Title>
              <p className="small text-muted">
                Pick a day and time you'll be at the SRC. Later, this can be visible to your friends.
              </p>

              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3" controlId="schedDate">
                  <Form.Label>Date</Form.Label>
                  <Form.Control
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                  />
                </Form.Group>

                <Row className="mb-3">
                  <Col xs={6}>
                    <Form.Group controlId="schedStart">
                      <Form.Label>Start time</Form.Label>
                      <Form.Control
                        type="time"
                        value={startTime}
                        onChange={(e) => setStartTime(e.target.value)}
                      />
                    </Form.Group>
                  </Col>
                  <Col xs={6}>
                    <Form.Group controlId="schedEnd">
                      <Form.Label>End time</Form.Label>
                      <Form.Control
                        type="time"
                        value={endTime}
                        onChange={(e) => setEndTime(e.target.value)}
                      />
                    </Form.Group>
                  </Col>
                </Row>

                <Form.Group className="mb-3" controlId="schedLocation">
                  <Form.Label>Location</Form.Label>
                  <Form.Select
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                  >
                    <option>SRC main weight room</option>
                    <option>SRC cardio area</option>
                    <option>Climbing wall</option>
                    <option>Indoor track</option>
                    <option>Other / specify below</option>
                  </Form.Select>
                </Form.Group>

                <Form.Group className="mb-3" controlId="schedNote">
                  <Form.Label>Note (optional)</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={2}
                    placeholder="Leg day, heavy bench, easy cardio, etc."
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                  />
                </Form.Group>

                <Form.Group className="mb-3" controlId="schedVisibility">
                  <Form.Label>Visibility</Form.Label>
                  <Form.Select
                    value={visibility}
                    onChange={(e) => setVisibility(e.target.value)}
                  >
                    <option value="friends">Friends</option>
                    <option value="private">Only me</option>
                  </Form.Select>
                  <Form.Text className="text-muted small">
                    Later, the Friends page can show "who's going when" using this.
                  </Form.Text>
                </Form.Group>

                {info && (
                  <p className="small text-success mb-2">{info}</p>
                )}
                {err && !loading && (
                  <p className="small text-danger mb-0">{err}</p>
                )}

                <div className="d-flex justify-content-end mt-3">
                  <Button
                    type="submit"
                    variant="maroon"
                    disabled={saving}
                  >
                    {saving ? "Saving…" : "Save slot"}
                  </Button>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
