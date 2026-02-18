import { useEffect, useMemo, useState } from "react"
import { Card, Row, Col, Badge, Alert, Button } from "react-bootstrap";
import { api } from "../api";
export default function Dashboard() {

  const [me, setMe] = useState(null);
  const [workouts, setWorkouts] = useState([]);
  const [err, setErr] = useState("");
  const [newClassName, setNewClassName] = useState("");
  const [myClasses, setMyClasses] = useState([]);
  const [enrolledClasses, setEnrolledClasses] = useState([]);
  const [statusMsg, setStatusMsg] = useState({ type: "", text: "" });
  const [deletingId, setDeletingId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editDate, setEditDate] = useState("");
  const [deletingSession, setDeletingSession] = useState({ classId: null, date: null });
  const [availableExercises, setAvailableExercises] = useState([]);
  const [selectedExercises, setSelectedExercises] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [confirmDeleteEx, setConfirmDeleteEx] = useState({ exIdx: null });

  // Here I am loading the current user and some of their recentmost workouts
  useEffect(() => {
    api("/auth/status")
      .then((resp) => {
        if (resp && resp.user) setMe(resp.user);
        else setMe(null);
      })
      .catch(() => setMe(null));

    api("/workouts")
      .then((resp) => {
        // BACKEND RETURNS: { items: [...] }
        const items = Array.isArray(resp?.items) ? [...resp.items] : [];
        items.sort((a, b) => {
          const date_a = (a.date || a.day || "");
          const date_b = (b.date || b.day || "");
          if (date_a === date_b) {
            return (b.created_at || "").localeCompare(a.created_at || "");
          }
          return date_b.localeCompare(date_a);
        });
        setWorkouts(items);
      })
      .catch((e) => {
        console.error(e);
        setErr("Could not load your workouts.");
        setWorkouts([]);
      });

    api('/exercises')
      .then(data => setAvailableExercises(data || []))
      .catch(err => console.error("Exercises load error:", err));

    api('/sessions').then(data => {
      if (data && data.length > 0) {
        setCurrentSessionId(data[0].id); 
      }
    });
  }, []);

  useEffect(() => {
    if (me?.role === "trainer") {
      api("/trainer-classes").then(resp => {
        if (resp?.items) setMyClasses(resp.items);
      });
    }
  }, [me]);

  useEffect(() => {
    if (me?.role === 'student') {
      api('/my-classes')
        .then(data => {
          if (Array.isArray(data)) {
            setEnrolledClasses(data);
          } else if (data?.items) {
            setEnrolledClasses(data.items);
          }
        })
        .catch(err => console.error("Failed to load enrolled classes:", err));
    }
  }, [me]);


  // These are helper functions that I created for calculating dashboard based statistics
  function parseDate(d) {
    if (!d) return null;

    const [y, m, day] = d.split("-").map(Number);
    if (!y || !m || !day) return null;

    return new Date(y, m - 1, day);
  }

  // This is a very compact and clean way of defining multiple variables and assigning them value simultaneous via a return/callback
  // I learnt that useMemo is a React hook which is used for 'memoization'
  // It basically caches a computed value so that React doesn't recompute it every time the component re-renders
  const {
    totalWorkouts,
    lastWorkout,
    weeklyMinutes,
    weeklyCount,
    weeklyDaysTrained,
  } = useMemo(() => {
    if (!workouts || workouts.length === 0) {
      return {
        totalWorkouts: 0,
        lastWorkout: null,
        weeklyMinutes: 0,
        weeklyCount: 0,
        weeklyDaysTrained: 0,
      };
    }

    const today = new Date();
    const sevenDaysAgo = new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate() - 6
    );

    // This is the main part where I am actually making most of my calculations and computations for the Dashboard
    let weeklyMinutes = 0;
    let weeklyCount = 0;
    const weeklyDates = new Set();

    // GOing over all the workouts to make the weekly minutes calculation
    for (const w of workouts) {
      const dateStr = w.date || w.day;
      const d = parseDate(dateStr);
      if (!d) continue;

      if (d >= sevenDaysAgo && d <= today) {
        weeklyMinutes += Number(w.duration_minutes || 0);
        weeklyCount += 1;
        weeklyDates.add(dateStr);
      }
    }

    return {
      totalWorkouts: workouts.length,
      lastWorkout: workouts[0] || null,
      weeklyMinutes: weeklyMinutes,
      weeklyCount: weeklyCount,
      weeklyDaysTrained: weeklyDates.size,
    };
  }, [workouts]);

  const handleCreateClass = async () => {
    if (!newClassName.trim()) {
      setStatusMsg({ type: "warning", text: "Please enter a class name." });
      return;
    }

    try {
      const response = await api("/classes/create", {
        method: "POST",
        body: ({ name: newClassName }),
      });

      if (response && !response.error) {
        setStatusMsg({ type: "success", text: `Class "${newClassName}" created successfully!` });
        setMyClasses([...myClasses, { id: response.class_id, name: newClassName }]);
        setNewClassName("");
      } else {
        setStatusMsg({ type: "danger", text: response.error || "Failed to create class." });      }
    } catch (e) {
      console.error(e);
      setStatusMsg({ type: "danger", text: "An error occurred while creating the class." });    }
  };

  const confirmDeleteClass = async (classId) => {
    try {
      const response = await api(`/classes/${classId}`, { method: "DELETE" });
      if (response && response.success) {
        setStatusMsg({ type: "success", text: "Class deleted successfully." });
        setMyClasses(myClasses.filter(c => c.id !== classId));
      } else {
        setStatusMsg({ type: "danger", text: response.error || "Failed to delete class." });
      }
    } catch  {
      setStatusMsg({ type: "danger", text: "An error occurred during deletion." });
    } finally {
      setDeletingId(null); // Reset confirmation state
    }
  };

  const handleUnenroll = async (classId) => {
    try {
      const response = await api(`/classes/${classId}/unenroll`, {
        method: "POST",
      });

      if (response && !response.error) {
        setStatusMsg({ type: "success", text: "Successfully unenrolled from class." });
        setEnrolledClasses(enrolledClasses.filter((cls) => cls.id !== classId));
      } else {
        setStatusMsg({ type: "danger", text: response.error || "Failed to unenroll." });
      }
    } catch (e) {
      console.error(e);
      setStatusMsg({ type: "danger", text: "An error occurred while unenrolling." });
    }
  };

  const handleSaveSession = async (classId) => {
    try {
      const sessionResp = await api(`/classes/${classId}/update-session`, {
        method: 'POST',
        body: { 
          session_date: editDate,
          exercises: selectedExercises
        }
      });

      const realSessionId = sessionResp.session_id;

      const allSetPromises = selectedExercises.flatMap((ex) => {
        return ex.sets.map((set, index) => {
          return api('/sets', {
            method: 'POST',
            body: {
              SessionID: realSessionId,
              ExerciseID: ex.id,
              SetNumber: set.setNumber || (index + 1),
              weight: parseFloat(set.weight) || 0,
              reps: parseInt(set.reps) || 0
            }
          });
        });
      });

      await Promise.all(allSetPromises);

      setMyClasses(prev => prev.map(cls => {
        if (cls.id === classId) {
          const currentDates = cls.session_dates && cls.session_dates !== "Not Set" 
            ? cls.session_dates.split(", ") 
            : [];
          
          if (!currentDates.includes(editDate)) {
            const updatedDates = [...currentDates, editDate].sort().join(", ");
            return { ...cls, session_dates: updatedDates };
          }
        }
        return cls;
      }));

      setStatusMsg({ type: "success", text: "Session saved!" });
      setEditingId(null);
    } catch (e) {
      setStatusMsg({ type: "danger", text: e.message });
    }
  };

  const handleDeleteSession = async (classId, dateToDelete) => {
    try {
      const response = await api(`/classes/${classId}/delete-session`, {
        method: "DELETE",
        body: { session_date: dateToDelete },
      });

      if (response && !response.error) {
        setMyClasses(prev => prev.map(cls => {
          if (cls.id === classId) {
            const dateArray = cls.session_dates.split(", ").filter(d => d !== dateToDelete);
            return {
              ...cls,
              session_dates: dateArray.length > 0 ? dateArray.join(", ") : "Not Set"
            };
          }
          return cls;
        }));
        setStatusMsg({ type: "success", text: `Session on ${dateToDelete} removed.` });
      } else {
        setStatusMsg({ type: "danger", text: response.error || "Delete failed." });
      }
    } catch {
      setStatusMsg({ type: "danger", text: "An error occurred during deletion." });
    } finally {
      setDeletingSession({ classId: null, date: null });
    }
  };

  const addSetToExercise = (exIdx) => {
    const newExercises = [...selectedExercises];
    const currentSets = newExercises[exIdx].sets || [];
    
    const newSet = {
      setNumber: currentSets.length + 1,
      weight: 0,
      reps: 0
    };
    
    newExercises[exIdx].sets = [...currentSets, newSet];
    setSelectedExercises(newExercises);
  };

  const updateSetData = (exIdx, setIdx, field, value) => {
    const newExercises = [...selectedExercises];
    let formattedValue = value;
    if (value !== "") {
      formattedValue = field === 'weight' ? parseFloat(value) : parseInt(value);
    }

    newExercises[exIdx].sets[setIdx][field] = formattedValue;
    setSelectedExercises(newExercises);
  };

  const removeSet = (exIdx, setIdx) => {
    const newExercises = [...selectedExercises];
    newExercises[exIdx].sets = newExercises[exIdx].sets
      .filter((_, i) => i !== setIdx)
      .map((set, i) => ({ ...set, setNumber: i + 1 }));
    setSelectedExercises(newExercises);
  };

  const removeExercise = async (exIdx, sessionId, exerciseId) => {
    if (sessionId && exerciseId) {
      try {
        const response = await api(`/sessions/${sessionId}/exercises/${exerciseId}`, { 
          method: 'DELETE' 
        });

        if (response && response.error) {
          setStatusMsg({ type: "danger", text: response.error });
          return;
        }

        setStatusMsg({ type: "success", text: "Exercise removed from database." });
      } catch (e) {
        console.error("Delete error:", e);
        setStatusMsg({ type: "danger", text: "Server error: Could not delete exercise." });
        return;
      }
    }

    const newExercises = selectedExercises.filter((_, i) => i !== exIdx);
    setSelectedExercises(newExercises);
    setConfirmDeleteEx({ exIdx: null });
  };
  
  return (
    <div className="dashboard-page py-3">
      <div className="d-flex justify-content-between align-items-baseline mb-3">
        <div>
          <h1 className="mb-1">Dashboard</h1>
          <p className="text-muted mb-0 small">Quick view of your gym grind.</p>
        </div>
        {me && (
          <div className="text-end small text-muted">
            Signed in as <strong>{me.username}</strong>
          </div>
        )}
      </div>

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

      <Row className="mb-3">

        {/* In this portion I am retrieving and displaying the weekly minutes */}
        <Col md={4} className="mb-3">
          <Card className="dashboard-card shadow-sm h-100">
            <Card.Body>
              <Card.Title as="h5" className="mb-1">This week at the SRC</Card.Title>
              <Card.Subtitle className="mb-2 text-muted small">Last 7 days</Card.Subtitle>

              <div className="display-6 fw-semibold mb-1">
                {weeklyMinutes} <span className="fs-6">min</span>
              </div>
              <p className="small text-muted mb-2">
                {weeklyCount === 0 ? "No sessions logged yet this week." : `Across ${weeklyCount} workout${
                      weeklyCount === 1 ? "" : "s"
                    } on ${weeklyDaysTrained} day${
                      weeklyDaysTrained === 1 ? "" : "s"
                    }.`}
              </p>
            </Card.Body>
          </Card>
        </Col>

        {/* Total workouts section*/}
        <Col md={4} className="mb-3">
          <Card className="dashboard-card shadow-sm h-100">
            <Card.Body>
              <Card.Title as="h5" className="mb-1">All-time sessions</Card.Title>
              <Card.Subtitle className="mb-2 text-muted small">Since you joined ShreddedNerds</Card.Subtitle>

              <div className="display-6 fw-semibold mb-1">{totalWorkouts}</div>

              <p className="small text-muted mb-2">
                {totalWorkouts === 0 ? "Log your first workout to start your history." : "Every logged session powers your dashboards and leaderboards."}
              </p>

              {weeklyDaysTrained > 0 && (
                <div className="small">
                  <Badge bg="light" text="dark" className="border me-1"> Active this week </Badge>
                  <span className="text-muted">{weeklyDaysTrained} training day{weeklyDaysTrained === 1 ? "" : "s"} so far.</span>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>

        {/* Last or latest workout */}
        <Col md={4} className="mb-3">
          <Card className="dashboard-card shadow-sm h-100">
            <Card.Body>
              <Card.Title as="h5" className="mb-1">Last workout</Card.Title>
              <Card.Subtitle className="mb-2 text-muted small">Let's see a quick recap</Card.Subtitle>

              {!lastWorkout ? (
                <p className="small text-muted mb-0"> You haven&apos;t logged a workout yet. Head to{" "}
                  <strong>Log Workouts</strong> to record your first SRC session.</p>
              ) : (
                <>
                
                  <div className="fw-semibold mb-1">
                    {(lastWorkout.date || lastWorkout.day)} · {lastWorkout.duration_minutes} min
                  </div>
                  <p className="small text-muted mb-2"> {lastWorkout.notes ? lastWorkout.notes : "No notes added for this workout."} </p>
                  <p className="small mb-0 text-muted">
                    Your detailed breakdown is available on the{" "}
                    <strong>History</strong> page (coming soon) and in the
                    Workouts section.
                  </p>
                </>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {me?.role === "trainer" && (
        <Row className="mb-4">
          <Col md={12}>
            <Card className="border-primary shadow-sm">
              <Card.Body>
                <Card.Title className="text-primary">Trainer Controls</Card.Title>
                <Card.Subtitle className="mb-3 text-muted">Create a new workout class for students</Card.Subtitle>
                <div className="d-flex gap-2">
                  <input
                    type="text"
                    className="form-control w-50"
                    placeholder="Enter Class Name (e.g. Advanced Powerlifting)"
                    value={newClassName}
                    onChange={(e) => setNewClassName(e.target.value)}
                  />
                  <button className="btn btn-primary" onClick={handleCreateClass}>
                    Create Class
                  </button>
                </div>
              </Card.Body>
            </Card>

            <Card className="mt-3 shadow-sm">
              <Card.Body>
                <Card.Title>Your Active Classes</Card.Title>
                <ul className="list-group list-group-flush">
                  {myClasses.map((c) => (
                    <li key={c.id} className="list-group-item py-3">
                      <div className="d-flex justify-content-between align-items-start">
                        <div className="flex-grow-1">
                          <span className="fw-bold fs-5">{c.name}</span>
                          
                          {/* Session History Section */}
                          <div className="text-muted small mt-2">
                            <label className="fw-bold d-block mb-1">Session History:</label>
                            <div className="d-flex flex-column gap-2 mt-1">
                              {c.session_dates && c.session_dates !== "Not Set" ? (
                                c.session_dates.split(", ").map((date, index) => (
                                  /* Changed to d-inline-block and added a max-width to keep them small */
                                  <div key={index} className="border rounded p-2 bg-white shadow-sm d-inline-block" style={{ minWidth: '200px', width: 'fit-content' }}>
                                    <div className="d-flex justify-content-between align-items-center gap-3">
                                      {/* Left Side: Date */}
                                      <Badge bg="info" className="px-2 py-1" style={{ fontSize: '0.75rem' }}>{date}</Badge>
                                      
                                      {/* Right Side: Buttons */}
                                      <div className="d-flex align-items-center gap-2">
                                        {deletingSession.classId === c.id && deletingSession.date === date ? (
                                          <div className="d-flex align-items-center gap-1">
                                            <Button variant="danger" size="sm" className="py-0 px-1" style={{ fontSize: '0.65rem' }} onClick={() => handleDeleteSession(c.id, date)}>Yes</Button>
                                            <Button variant="secondary" size="sm" className="py-0 px-1" style={{ fontSize: '0.65rem' }} onClick={() => setDeletingSession({ classId: null, date: null })}>No</Button>
                                          </div>
                                        ) : (
                                          <>
                                            <Button 
                                              variant="link" 
                                              className="p-0 text-decoration-none text-muted d-flex align-items-center" 
                                              onClick={async () => {
                                                const targetId = c.id;
                                                const targetDate = date;

                                                setEditingId(targetId);
                                                setEditDate(targetDate);
                                                setSelectedExercises([]);

                                                try {
                                                  const response = await api(`/sessions/details?date=${targetDate}&classId=${targetId}`);
                                                  if (response && Array.isArray(response)) {
                                                      const grouped = response.reduce((acc, row) => {
                                                          let ex = acc.find(e => e.name === row.ExerciseName);
                                                          if (!ex) {
                                                              ex = { name: row.ExerciseName, category: row.Category, sets: [] };
                                                              acc.push(ex);
                                                          }
                                                          if (row.SetNumber !== null) {
                                                              ex.sets.push({
                                                                  setNumber: row.SetNumber,
                                                                  weight: row.Weight,
                                                                  reps: row.Reps
                                                              });
                                                          }
                                                          return acc;
                                                      }, []);
                                                      setSelectedExercises(grouped);
                                                  }
                                                } catch (err) {
                                                  console.error("Failed to load session details", err);
                                                }
                                              }}
                                            >
                                              <i className="bi bi-pencil-square me-1"></i>
                                              <span>Edit</span>
                                            </Button>
                                            
                                            <Button 
                                              variant="link" 
                                              className="p-0 text-decoration-none text-danger d-flex align-items-center" 
                                              onClick={() => setDeletingSession({ classId: c.id, date: date })}
                                            >
                                              <i className="bi bi-trash me-1" style={{ fontSize: '0.8rem' }}></i>
                                              <span style={{ fontSize: '0.75rem' }}>Delete</span>
                                            </Button>
                                          </>
                                        )}
                                      </div>
                                    </div>

                                    {/* Exercises Text - only shows if exists, kept small */}
                                    {c.exercises && (
                                      <div className="mt-1 text-dark pt-1 border-top" style={{ fontSize: '0.75rem', fontStyle: 'italic' }}>
                                        {c.exercises}
                                      </div>
                                    )}
                                  </div>
                                ))
                              ) : (
                                <Badge bg="secondary">No Sessions</Badge>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Main Class Actions (The buttons that were missing/squished) */}
                        <div className="d-flex gap-2 ms-3">
                          <Button 
                            variant="outline-secondary" 
                            size="sm" 
                            onClick={() => {
                              if (editingId === c.id) {
                                setEditingId(null);
                                setEditDate("");
                                setSelectedExercises([]);
                              } else {
                                setEditingId(c.id);
                                setEditDate("");
                                setSelectedExercises([]);
                              }
                            }}
                          >
                            {editingId === c.id ? "Close" : "Add Session"}
                          </Button>

                          {deletingId === c.id ? (
                            <div className="bg-light p-1 border rounded d-flex gap-1 align-items-center">
                              <span className="small text-danger fw-bold px-1">Class?</span>
                              <Button variant="danger" size="sm" onClick={() => confirmDeleteClass(c.id)}>Yes</Button>
                              <Button variant="secondary" size="sm" onClick={() => setDeletingId(null)}>No</Button>
                            </div>
                          ) : (
                            <Button variant="outline-danger" size="sm" onClick={() => setDeletingId(c.id)}>
                              Delete Class
                            </Button>
                          )}
                        </div>
                      </div>

                      {/* The Edit Panel */}
                      {editingId === c.id && (
                        <div className="mt-3 p-3 border rounded bg-light shadow-sm">
                          <h6 className="small fw-bold text-uppercase text-muted mb-3 border-bottom pb-2">
                            Update Session Details
                          </h6>
                          <Row className="g-3">
                            <Col md={4}>
                              <div className="form-group">
                                <label className="small fw-bold mb-1 d-block">Session Date</label>
                                <input 
                                  type="date" 
                                  className="form-control form-control-sm" 
                                  value={editDate} 
                                  onChange={(e) => setEditDate(e.target.value)} 
                                />
                              </div>
                            </Col>

                            <div className="mb-3 p-2 border rounded bg-white">
                              <label className="small fw-bold mb-1 d-block text-primary">Add New Exercise to Session</label>
                              <div className="d-flex gap-2">
                                <select 
                                  className="form-select form-select-sm"
                                  onChange={(e) => {
                                    const exId = parseInt(e.target.value);
                                    if (!exId) return;
                                    const exObj = availableExercises.find(a => a.id === exId);
                                    if (exObj) {
                                      setSelectedExercises([...selectedExercises, { 
                                        id: exObj.id, 
                                        name: exObj.name, 
                                        sets: [{ setNumber: 1, weight: 0, reps: 0 }] 
                                      }]);
                                    }
                                    e.target.value = "";
                                  }}
                                >
                                  <option value="">-- Select Exercise to Add --</option>
                                  {availableExercises
                                    .filter(a => !selectedExercises.some(se => se.id === a.id)) // Hide already added
                                    .map(a => (
                                      <option key={a.id} value={a.id}>{a.name}</option>
                                    ))
                                  }
                                </select>
                              </div>
                            </div>
                            
                            <Col md={8}>
                              <label className="small fw-bold mb-1 d-block">Exercises in this Session</label>
                              <div className="exercise-edit-list">
                                {selectedExercises.map((ex, exIdx) => (
                                  <div key={ex.id || exIdx} className="border rounded p-3 mb-3 bg-white shadow-sm">
                                    <div className="d-flex justify-content-between align-items-center border-bottom pb-2 mb-3">
                                      <div>
                                        <h5 className="h6 mb-0 fw-bold text-primary">{ex.name}</h5>
                                      </div>
                                      <div className="d-flex align-items-center">
                                        {confirmDeleteEx.exIdx === exIdx ? (
                                          <div className="bg-light p-1 border rounded d-flex gap-1 align-items-center">
                                            <span className="small text-danger fw-bold px-1">Remove all sets?</span>
                                            <Button 
                                              variant="danger" 
                                              size="sm" 
                                              onClick={() => removeExercise(exIdx, currentSessionId, ex.id)}
                                            >
                                              Yes
                                            </Button>
                                            <Button 
                                              variant="secondary" 
                                              size="sm" 
                                              onClick={() => setConfirmDeleteEx({ exIdx: null })}
                                            >
                                              No
                                            </Button>
                                          </div>
                                        ) : (
                                          <Button 
                                            variant="outline-danger" 
                                            size="sm" 
                                            onClick={() => setConfirmDeleteEx({ exIdx: exIdx })}
                                          >
                                            <i className="bi bi-trash me-1"></i>
                                            Remove
                                          </Button>
                                        )}
                                      </div>
                                    </div>
                                    
                                    {ex.sets.map((set, setIdx) => (
                                      <Row key={setIdx} className="mb-3 align-items-end g-2">
                                        <Col xs={2}>
                                          <label className="small text-muted d-block mb-1">Set</label>
                                          <input 
                                            type="text" 
                                            readOnly 
                                            className="form-control form-control-sm bg-light text-center fw-bold" 
                                            value={set.setNumber} 
                                          />
                                        </Col>
                                        <Col xs={4}>
                                          <label className="small text-muted d-block mb-1">Weight (kg/lbs)</label>
                                          <input 
                                            type="number" 
                                            className="form-control form-control-sm" 
                                            placeholder="0"
                                            value={set.weight}
                                            onChange={(e) => updateSetData(exIdx, setIdx, 'weight', e.target.value)}
                                          />
                                        </Col>
                                        <Col xs={4}>
                                          <label className="small text-muted d-block mb-1">Reps</label>
                                          <input 
                                            type="number" 
                                            className="form-control form-control-sm" 
                                            placeholder="0"
                                            value={set.reps}
                                            onChange={(e) => updateSetData(exIdx, setIdx, 'reps', e.target.value)}
                                          />
                                        </Col>
                                        <Col xs={2}>
                                          <Button 
                                            variant="outline-danger" 
                                            size="sm" 
                                            className="w-100" 
                                            onClick={() => removeSet(exIdx, setIdx)}
                                          >
                                            &times;
                                          </Button>
                                        </Col>
                                      </Row>
                                    ))}
                                    
                                    <Button 
                                      variant="outline-primary" 
                                      size="sm" 
                                      className="mt-1"
                                      onClick={() => addSetToExercise(exIdx)}
                                    >
                                      + Add Set
                                    </Button>
                                  </div>
                                ))}
                              </div>
                            </Col>
                          </Row>
                          
                          <div className="mt-3 pt-3 border-top text-end">
                            <Button variant="success" size="sm" onClick={() => handleSaveSession(c.id)}>
                              Save Session Changes
                            </Button>
                          </div>
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {me?.role === 'student' && (
        <Row className="mb-4">
          <Col md={12}>
            <Card className="shadow-sm border-info">
              <Card.Body>
                <Card.Title className="text-info">My Enrolled Classes</Card.Title>
                <Card.Subtitle className="mb-3 text-muted small">
                  Your current schedule from the SRC
                </Card.Subtitle>
                
                {enrolledClasses.length === 0 ? (
                  <p className="text-muted italic small">You haven't joined any classes yet.</p>
                ) : (
                  <Row>
                    {enrolledClasses.map((cls) => (
                      <Col key={cls.id} md={4} className="mb-3">
                        <div className="p-3 rounded border border-info bg-light h-100">
                          <h6 className="mb-1 fw-bold">{cls.name}</h6>
                          <div className="small text-muted">Trainer: {cls.trainer_name}</div>
                          <div className="session-history">
                            <label className="d-block small fw-bold text-muted">Session History:</label>
                            {cls.session_dates && cls.session_dates !== "Not Set" ? (
                              <div className="d-flex flex-wrap gap-1">
                                {cls.session_dates.split(', ').map((date, index) => (
                                  <Badge key={index} bg="light" text="dark" className="border">
                                    {date}
                                  </Badge>
                                ))}
                              </div>
                            ) : (
                              <span className="text-muted small italic">No sessions recorded</span>
                            )}
                          </div>
                          <Button 
                            variant="outline-danger" 
                            size="sm" 
                            className="mt-3 w-100"
                            onClick={() => handleUnenroll(cls.id)}
                          >
                            Leave Class
                          </Button>
                        </div>
                      </Col>
                    ))}
                  </Row>
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Recent mini list at bottom */}
      <Row>
        <Col md={8}>
          <Card className="dashboard-card shadow-sm">
            <Card.Body>
              <Card.Title as="h5" className="mb-2">
                Recent workouts
              </Card.Title>
              <p className="small text-muted">
                A quick glance at your last few sessions.
              </p>

              {workouts.length === 0 && (
                <p className="small text-muted mb-0">
                  Nothing here yet — log a workout to see it appear.
                </p>
              )}

              {/* for Dashboard I am only showing 5 recent most workouts */}
              {workouts.slice(0, 5).map((workout) => (
                <div key={workout.id} className="d-flex justify-content-between small mb-2">
                  <div>
                    <div className="fw-semibold">{workout.date || workout.day}</div>
                    <div className="text-muted">
                      {workout.duration_minutes} min
                      {workout.notes ? ` · ${workout.notes.slice(0, 40)}…` : ""}
                    </div>
                  </div>
                  <div className="text-end text-muted">
                    <div>ID #{workout.id}</div>
                  </div>
                </div>
              ))}
            </Card.Body>
          </Card>
        </Col>

        {/* These are just some notes about workins of Dashboard which I added as a seperate card */}
        <Col md={4} className="mt-3 mt-md-0">
          <Card className="dashboard-card shadow-sm h-100">
            <Card.Body className="small text-muted">
              <Card.Title as="h6" className="mb-2">
                How this dashboard works
              </Card.Title>
              <ul className="mb-0 ps-3">
                <li>All stats are computed from your logged workouts.</li>
                <li>
                  &ldquo;This week&rdquo; means today plus the previous 6 days.
                </li>
                <li>
                  Every new session updates this page, your history, and (later)
                  leaderboards.
                </li>
              </ul>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
}