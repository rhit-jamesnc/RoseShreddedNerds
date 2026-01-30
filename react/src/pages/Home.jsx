import { Row, Col, Button, Card, Badge } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "../api";

export default function Home() {

  const navigate = useNavigate();

  // These are the state variables I create to store the statistics which are updated dynamically
  const [totalMinutes, setTotalMinutes] = useState(null);
  const [topBig3, setTopBig3] = useState(null);
  const [streak, setStreak] = useState(null);

  // This is the side effect function which would carry out the task based on the function I define below
  useEffect(() => {
    loadStats();
  }, []);

  async function loadStats() {
    try {
      // Fetch the workouts for the year from backend
      const { items: ws} = await api("/workouts/campus");

      if (Array.isArray(ws)) {
        // Computes the total number of mins spent in SRC
        const mins = ws.reduce((sum, workout) => sum + (Number(workout.duration_minutes) || 0), 0);
        setTotalMinutes(mins);

        // This part just computes the streak
        setStreak(computeStreak(ws));
      }

      // Here I am computing the Big-3 Leaderboard
      const { items: leaderboard } = await api("/leaderboards/big3");
      if (Array.isArray(leaderboard) && leaderboard.length > 0) {
        setTopBig3(leaderboard[0].big3_total_kg);
      }
    } catch (err) {
      console.log("Loading error", err);
    }
  }

  // A function I created to compute the streak (days with at least 1 workout done)
  function computeStreak(workouts) {

    if (!workouts.length) return 0;

    // Extract only the dates form the workouts object
    const dates = [...new Set(workouts.map(w => w.date || w.day))].sort().reverse();

    let streak = 1;
    for (let i = 1; i < dates.length; i++) {
      const d1 = new Date(dates[i - 1]);
      const d2 = new Date(dates[i]);

      // Just checks for differnece in terms of number of seconds in a day to know whether or not it is another day's stream or no
      const diff = (d1 - d2) / (1000 * 60 * 60 * 24);

      if (diff === 1) streak++;
      else break;
    }
    return streak;
  }

  return (
    <div className="home-page py-4">
      <Row className="align-items-center">
        <Col md={6} className="mb-4 mb-md-0">
          <p className="text-uppercase text-mutated small mb-1">
            The perfect way to make workout fun — For Rose-Hulman Students, By Rose-Hulman Students
          </p>

          <h1 className="display-5 fw-bold mb-3">
            From the Classroom to the Weight Room — <span className="highlight">We Compete Smarter!</span>
          </h1>

          <p className="lead text-muted">
            ShreddedNerds tracks your gym time, big-3 totals, and SRC schedule — all in one scoreboard built just for Rose Students who are looking for a heavy challenge!
          </p>

          <div className="d-flex flex-wrap gap-2 mt-3">
            <Button variant="maroon" onClick={() => navigate("/register")}>Get Started</Button>
            <Button variant="outline-maroon" onClick={() => navigate("/dashboard")}>View my dashboard</Button>
          </div>

          <ul className="mt-4 list-unstyled small text-muted">
            <li>• Log sets, reps, and weights in seconds</li>
            <li>• Auto-compute estimated 1RM &amp; big-3 total</li>
            <li>• See when friends are heading to the SRC</li>
          </ul>
        </Col>

        <Col md={6}>
          <Card className="home-card shadow-sm">

            <Card.Header className="d-flex justify-content-between align-items-center">
              <span className="fw-semibold">This week at the SRC</span>
              <Badge bg="light" text="dark" className="border small">
                Live
              </Badge>
            </Card.Header>

            <Card.Body>

              { /* Total Minutes */ }
              <div className="d-flex justify-content-between small text-muted mb-2">
                <span>Campus minutes logged</span>
                <span className="fw-semibold text-dark">{totalMinutes !== null ? `${totalMinutes} min` : "—"}</span>
              </div>
              <div className="progress mb-3" style={{ height: 6 }}>
                <div className="progress-bar bg-maroon" role="progressbar" style={{ width: totalMinutes ? `${Math.min(totalMinutes / 20, 100)}%` : "0%" }} />
              </div>

               {/* --- Big-3 Total --- */}
              <div className="d-flex justify-content-between small text-mutated mb-1">
                <span>Top big-3 total</span>
                <span className="fw-semibold text-dark">{topBig3 !== null ? `${topBig3} kg` : "—"}</span>
              </div>
              <div className="d-flex justify-content-between small text-mutated mb-3">
                <span>Most consistent streak</span>
                <span className="fw-semibold text-dark">{streak !== null ? `${streak} days` : "—"}</span>
              </div>

              <hr />

              <p className="small mb-2 text-muted">
                These stats update automatically as you log workouts.
              </p>
              <p className="small mb-0 text-muted">
                Start lifting — and watch your totals climb!
              </p>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
}