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
        console.log("Dashboard workouts resp:", resp);   // ← debug log
        setWorkouts(items);
      })
      .catch((e) => {
        console.error(e);
        setErr("Could not load your workouts.");
        setWorkouts([]);
      });
  }, []);

  useEffect(() => {
    console.log("Current User for Class Fetch:", me); // Check this in F12 console
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
          console.log("Enrolled classes data:", data);
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
        body: JSON.stringify({ name: newClassName }),
      });

      if (response && !response.error) {
        setStatusMsg({ type: "success", text: `Class "${newClassName}" created successfully!` });
        setMyClasses([...myClasses, { id: response.class_id, name: newClassName }]);        setMyClasses([...myClasses, { id: response.class_id, name: newClassName }]);
        setNewClassName(""); // Clear the input
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
                  {myClasses.map(c => (
                    <li key={c.id} className="list-group-item d-flex justify-content-between align-items-center py-3">
                      <div>
                        <span className="fw-bold">{c.name}</span> <span className="text-muted small">#({c.id})</span>
                      </div>
                      
                      {deletingId === c.id ? (
                        <div className="bg-light p-2 border rounded d-flex align-items-center gap-2">
                          <span className="small text-danger fw-bold">Delete?</span>
                          <Button variant="danger" size="sm" onClick={() => confirmDeleteClass(c.id)}>Yes</Button>
                          <Button variant="secondary" size="sm" onClick={() => setDeletingId(null)}>No</Button>
                        </div>
                      ) : (
                        <Button 
                          variant="outline-danger" 
                          size="sm" 
                          onClick={() => setDeletingId(c.id)}
                        >
                          Delete
                        </Button>
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
                          <div className="text-muted mt-2" style={{ fontSize: '0.7rem' }}>
                            Class ID: {cls.id}
                          </div>
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