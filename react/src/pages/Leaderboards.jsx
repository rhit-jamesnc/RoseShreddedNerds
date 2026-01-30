import { useEffect, useMemo, useState } from "react";
import { Card, Row, Col, Table, Badge } from "react-bootstrap";
import { api } from "../api";

// src/pages/Leaderboards.jsx
export default function Leaderboards() {

  const [me, setMe] = useState(null);
  const [big3, setBig3] = useState([]);
  const [err, setErr] = useState("");

  // Load current user and the big-3 leaderboard
  useEffect(() => {
  // Load current user
  api("/auth/status")
    .then((resp) => {
      if (resp && resp.user) setMe(resp.user);
      else setMe(null);
    })
    .catch(() => setMe(null));

  // Load Big-3 leaderboard
  api("/leaderboards/big3")
    .then((resp) => {
      // BACKEND RETURNS: { items: [...] }
      const items = Array.isArray(resp?.items) ? resp.items : [];
      setBig3(items);
      console.log("Leaderboards big3 resp:", resp);   // ← debug log
    })
    .catch((e) => {
      console.error(e);
      setErr("Could not load leaderboards.");
      setBig3([]);
    });
}, []);

  // This variable/object stores the user's own performance / big3 stat
  const myRank = useMemo(() => {
    if (!me || !big3 || big3.length === 0) return null;
    const idx = big3.findIndex((resp) => resp.username === me.username);

    if (idx === -1) return null;
    return {
      rank: idx + 1,
      total: big3.length,
      entry: big3[idx],
    };
  }, [me, big3]);


  return (
    <div className="leaderboards-page py-3">
      <div className="d-flex justify-content-between align-items-baseline mb-3">
        <div>
          <h1 className="mb-1">Leaderboards</h1>
          <p className="text-muted mb-0 small">
            Campus-wide big-3 totals: Squat + Bench + Deadlift (estimated 1RM).
          </p>
        </div>
        {me && (
          <div className="text-end small text-muted">
            Signed in as <strong>{me.username}</strong>
          </div>
        )}
      </div>

      {err && (
        <div className="alert alert-danger py-2" role="alert">
          {err}
        </div>
      )}

      <Row className="mb-3">
        <Col md={6} className="mb-3">
          <Card className="leader-card shadow-sm h-100">
            <Card.Body>
              <Card.Title as="h5" className="mb-1">
               My Big-3 Total (kg)
              </Card.Title>
              <Card.Subtitle className="mb-2 text-muted small">Sum of my best Squat, Bench, and Deadlift (estimated 1RM).</Card.Subtitle>

              {myRank ? (
                <>
                  <div className="display-6 fw-semibold mb-1">
                    #{myRank.rank}{" "}
                    <span className="fs-6 text-muted">/ {myRank.total} lifter{myRank.total === 1 ? "" : "s"}</span>
                  </div>
                  <p className="small text-muted mb-0">
                    Your Big-3 total:{" "}
                    <strong>{myRank.entry.big3_total_kg.toFixed(1)} kg</strong>
                  </p>
                </>
              ) : big3.length === 0 ? (
                <p className="small text-muted mb-0">No big-3 data yet. Log Squat, Bench, and Deadlift workouts to appear on the board.</p>
              ) : (
                <p className="small text-muted mb-0">Log Squat, Bench, and Deadlift PRs to show up on this board.</p>
              )}
            </Card.Body>
          </Card>
        </Col>

        <Col md={6} className="mb-3">
          <Card className="leader-card shadow-sm h-100">
            <Card.Body className="small text-muted">
              <Card.Title as="h6" className="mb-2">
                How this leaderboard works
              </Card.Title>
              <ul className="mb-0 ps-3">
                <li>
                  For each lifter, we store their best estimated 1RM (1 Rep Max) for Squat,
                  Bench, and Deadlift.
                </li>
                <li>
                  Your <strong>Big-3 total</strong> is the sum of those three
                  best 1RMs.
                </li>
                <li>
                  1RM is estimated using the Epley formula from your logged sets
                  & reps.
                </li>
                <li>
                  Log heavier sets to update your personal records and move up
                  the board.
                </li>
              </ul>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Card className="leader-card shadow-sm">
        <Card.Body>
          <Card.Title as="h5" className="mb-3">
            Big-3 Total — Campus Rankings
          </Card.Title>

          {big3.length === 0 ? (
            <p className="small text-muted mb-0">
              No lifters on the board yet. Once people start logging PRs, the
              top totals will show up here.
            </p>
          ) : (
            <div className="table-responsive">
              <Table hover size="sm" className="align-middle mb-0">
                <thead>
                  <tr>
                    <th style={{ width: "10%" }}>Rank</th>
                    <th style={{ width: "40%" }}>Lifter</th>
                    <th style={{ width: "50%" }}>Big-3 total (kg)</th>
                  </tr>
                </thead>
                <tbody>
                  {big3.map((row, index) => {
                    const isMe = me && row.username === me.username;
                    return (
                      <tr key={row.username} className={isMe ? "leader-me-row" : ""}>
                        <td><span className="fw-semibold">#{index + 1}</span></td>
                        <td>
                          <div className="fw-semibold">
                            {row.display_name || row.username}
                          </div>
                          <div className="text-muted small">
                            @{row.username}
                            {isMe && (
                              <Badge bg="light" text="dark" className="ms-2 border">You</Badge>
                            )}
                          </div>
                        </td>
                        <td>
                          <span className="fw-semibold">
                            {row.big3_total_kg.toFixed(1)} kg
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </Table>
            </div>
          )}
        </Card.Body>
      </Card>
    </div>
  );
}
