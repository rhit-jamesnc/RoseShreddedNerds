import { useEffect, useState } from "react";
import { Card, Container, Table, Badge, Button } from "react-bootstrap";
import { api } from "../api";

export default function ClassList() {
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [me, setMe] = useState(null);

  useEffect(() => {
    api("/auth/status")
      .then((resp) => setMe(resp?.user || null))
      .catch(() => setMe(null));

    fetchClasses();
  }, []);

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
      const response = await api(`/classes/${classId}/enroll`, {
        method: "POST",
      });

      if (response.success) {
        alert("Success! You are now enrolled in the class.");
      } else {
        alert(response.error || "Could not enroll in class.");
      }
    } catch (e) {
      console.error("Enrollment error:", e);
      alert("An error occurred. Please try again later.");
    }
  }

  return (
    <Container className="py-4">
      <h2 className="mb-4">Available Classes</h2>
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
                {classes.map((c) => (
                  <tr key={c.id}>
                    <td className="fw-bold">{c.name}</td>
                    <td>{c.trainer_username || "Unknown"}</td>
                    <td>
                      <Badge bg="secondary">#{c.session_id || "N/A"}</Badge>
                    </td>
                    <td className="text-end">
                      {me?.role === "student" && (
                        <Button 
                          variant="outline-success" 
                          size="sm"
                          onClick={() => handleJoinClass(c.id)}
                        >
                          Join Class
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
}