import { useEffect, useState } from "react";
import { Card, Container, Table, Badge, Button, Alert } from "react-bootstrap";
import { api } from "../api";

export default function ClassList() {
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [me, setMe] = useState(null);
  const [status, setStatus] = useState(null);
  const [joinedClasses, setJoinedClasses] = useState(new Set());

  useEffect(() => {
    api("/auth/status")
      .then((resp) => {
        const user = resp?.user || null;
        setMe(user);
        if (user?.role?.toLowerCase() === "student") {
          fetchMyEnrollments(user.sql_id);
        }
      })
      .catch(() => setMe(null));
      
    fetchClasses();
  }, []);

  const fetchMyEnrollments = () => {
    api(`/my-classes`)
      .then((resp) => {
        if (Array.isArray(resp)) {
          // Map the IDs of enrolled classes into a new Set
          const enrolledIds = new Set(resp.map(c => c.id));
          setJoinedClasses(enrolledIds);
        }
      })
      .catch((e) => console.error("Failed to load your enrollments", e));
  };

  const fetchClasses = () => {
    setLoading(true);
    api("/classes")
      .then((resp) => {
        if (Array.isArray(resp)) setClasses(resp);
        else if (resp?.items) setClasses(resp.items);
      })
      .catch((e) => console.error("Failed to load classes", e))
      .finally(() => setLoading(false));
  };

  const handleJoinClass = async (classId) => {
    try {
      await api(`/classes/${classId}/enroll`, {
        method: "POST",
      });

      setJoinedClasses((prev) => new Set(prev).add(classId));
      setStatus({ type: "success", msg: "Successfully enrolled!" });
      fetchMyEnrollments();

    } catch (e) {
      const errorMsg = e.message || "A server error occurred.";
      setStatus({ type: "danger", msg: errorMsg });
      
      if (errorMsg.includes("Already enrolled")) {
         setJoinedClasses((prev) => new Set(prev).add(classId));
      }
    }
  };

  return (
    <Container className="py-4">
      <h2 className="mb-4">Available Classes</h2>

      {status && (
        <Alert variant={status.type} className="mb-3">
          {status.msg}
        </Alert>
      )}

      <Card className="shadow-sm">
        <Card.Body>
          {loading ? (
            <p>Loading classes...</p>
          ) : classes.length === 0 ? (
            <p className="text-muted">No classes have been created yet.</p>
          ) : (
            <Table hover responsive verticalalign="middle">
              <thead>
                <tr>
                  <th>Class Name</th>
                  <th>Trainer</th>
                  <th>Session ID</th>
                  <th className="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                {classes.map((c) => {
                  const isJoined = joinedClasses.has(c.id);

                  return (
                    <tr key={c.id}>
                      <td className="fw-bold">{c.name}</td>
                      {/* Use trainer_name if that is what your SQL query returns */}
                      <td>{c.trainer_name || c.trainer_username || "Unknown"}</td>
                      <td>
                        <Badge bg="secondary">#{c.id || "N/A"}</Badge>
                      </td>
                      <td className="text-end">
                        {me?.role?.toLowerCase() === "student" && (
                          <Button
                            variant={isJoined ? "success" : "outline-success"}
                            size="sm"
                            disabled={isJoined}
                            onClick={() => handleJoinClass(c.id)}
                          >
                            {isJoined ? "Enrolled" : "Join Class"}
                          </Button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
}