import { useEffect, useState } from "react";
import { Card, Table, Badge } from "react-bootstrap";
import { api } from "../api";

export default function PersonalRecords() {

  const [me, setMe] = useState(null);
  const [records, setRecords] = useState([]);
  const [err, setErr] = useState("");

  useEffect(() => { 
    api("/auth/status")
      .then((resp) => setMe(resp?.user || null))
      .catch(() => setMe(null));

    api("/personal-records") //loading pr from server
      .then((resp) => {
        const items = Array.isArray(resp?.items) ? resp.items : [];
        setRecords(items);
      })
      .catch((e) => {
        console.error(e);
        setErr("Could not load personal records.");
      });
  }, []);

  return (
    <div className="personal-records-page py-3">
      <div className="d-flex justify-content-between align-items-baseline mb-3">
        <div>
          <h1 className="mb-1">Personal Records</h1>
          <p className="text-muted mb-0 small">
            Your best lifts across all exercises
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

      <Card className="shadow-sm">
        <Card.Body>
          <Card.Title as="h5" className="mb-3">
            All-Time PRs
          </Card.Title>

          {records.length === 0 ? (
            <p className="small text-muted mb-0">
              No personal records yet. Log workouts to start tracking your PRs!
            </p>
          ) : (
            <div className="table-responsive">
              <Table hover size="sm" className="align-middle mb-0">
                <thead>
                  <tr>
                    <th>Exercise</th>
                    <th>Category</th>
                    <th>Best Weight (kg)</th>
                    <th>Best Reps</th>
                    <th>Est. 1RM (kg)</th>
                    <th>Last Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((r) => (
                    <tr key={r.exercise_name}>
                      <td className="fw-semibold">{r.exercise_name}</td>
                      <td>
                        <Badge
                          bg={r.category === "strength" ? "dark" : "info"}
                          className="text-capitalize"
                        >
                          {r.category}
                        </Badge>
                      </td>
                      <td>{r.best_weight_kg}</td>
                      <td>{r.best_reps}</td>
                      <td className="fw-semibold">{r.best_1rm_kg.toFixed(1)}</td>
                      <td className="text-muted small">
                        {r.updated_at
                          ? new Date(r.updated_at).toLocaleDateString()
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          )}
        </Card.Body>
      </Card>
    </div>
  );
}
