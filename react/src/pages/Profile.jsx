import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Form, Button, Card, Alert, Row, Col, Spinner } from "react-bootstrap";
import { api } from "../api";

const USERNAME_RE = /^[a-zA-Z][a-zA-Z0-9_-]{2,19}$/;

export default function Profile() {
    const navigate = useNavigate();

    //Form Fields
    const [username, setUsername] = useState("");
    const [firstName, setFirstName] = useState("");
    const [lastName, setLastName] = useState("");
    const [dob, setDob] = useState("");
    const [weight, setWeight] = useState("");
    const [password, setPassword] = useState("");

    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [validated, setValidated] = useState(false);
    const [error, setError] = useState("");
    const [info, setInfo] = useState("");

    useEffect(() => {
    let alive = true;

    async function loadProfile() {
      setLoading(true);
      setError("");
      setInfo("");

      try {
        const resp = await api("/profile");
        const user = resp?.user;

        if (!user) {
          navigate("/login");
          return;
        }

        // Normalize keys just in case backend returns different casing
        const Username = user.Username ?? "";
        const FName = user.FName ?? "";
        const LName = user.LName ?? "";
        const DOB = user.DOB ?? "";
        const Weight = user.Weight ?? "";

        if (!alive) return;

        setUsername(Username);
        setFirstName(FName || "");
        setLastName(LName || "");
        setDob(DOB || "");
        setWeight(Weight === null || Weight === undefined ? "" : String(Weight));

        // Never prefill password
        setPassword("");
      } catch (err) {
            console.error("Profile load failed:", err);
            navigate("/login");
      } finally {
            if (alive) setLoading(false);
      }
    }

    loadProfile();
    return () => {
      alive = false;
    };
  }, [navigate]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setInfo("");
    setValidated(true);

    if (!username.trim()) {
        setError("Please enter a username.");
        return;
    }
    if (!USERNAME_RE.test(username.trim())) {
    setError("Username must start with a letter, be 3-20 characters, and contain only letters, numbers, hyphens, or underscores.");
    return;
    }

    if (!firstName.trim() || !lastName.trim()) {
      setError("Please enter your first and last name.");
      return;
    }

    if (password.trim().length > 0 && password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    if (weight && (isNaN(+weight) || +weight < 50 || +weight > 300)) {
      setError("Weight must be a number between 50 and 500 lbs.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        username: username.trim(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      };

      if (dob) payload.dob = dob;
      if (weight) payload.weight = Number(weight);

      if (password.trim().length > 0) {
        payload.password = password;
      }

      const resp = await api("/profile", {
        method: "PUT",
        body: payload,
      });

      if (resp?.user) {
        setInfo("Profile updated successfully!");
        // Clear password field after save
        setPassword("");
      } else {
        setInfo("Profile updated.");
        setPassword("");
      }
    } catch (err) {
      setError(err.message || "There was an error updating your profile.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="auth-page">
        <Card className="auth-card shadow-sm">
          <Card.Body className="d-flex align-items-center gap-2">
            <Spinner animation="border" size="sm" />
            <div>Loading your profile...</div>
          </Card.Body>
        </Card>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <Card className="auth-card shadow-sm">
        <Card.Body>
          <h2 className="mb-1">Your Profile</h2>
          <p className="text-muted mb-3 small">
            Update your details anytime. Leave the password blank if you don't want to change it.
          </p>

          {error && <Alert variant="danger" className="py-2">{error}</Alert>}
          {info && <Alert variant="success" className="py-2">{info}</Alert>}

          <Form onSubmit={handleSubmit} autoComplete="off">
            <Form.Group className="mb-3" controlId="username">
                <Form.Label>Username</Form.Label>
                <Form.Control
                    type="text"
                    placeholder="johnsnow"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    isInvalid={validated && !username.trim()}
                />
                <Form.Control.Feedback type="invalid">
                    Username is required.
                </Form.Control.Feedback>

                {!(!username.trim() && validated) && (
                    <Form.Text className="text-muted">
                    Choose a new username (must be unique).
                    </Form.Text>
                )}
            </Form.Group>

            <Row>
              <Col xs={12} md={6}>
                <Form.Group className="mb-3" controlId="firstName">
                  <Form.Label>First name</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="Aaryan"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    isInvalid={validated && !firstName.trim()}
                  />
                  <Form.Control.Feedback type="invalid">
                    First name is required.
                  </Form.Control.Feedback>
                </Form.Group>
              </Col>

              <Col xs={12} md={6}>
                <Form.Group className="mb-3" controlId="lastName">
                  <Form.Label>Last name</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="idk"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    isInvalid={validated && !lastName.trim()}
                  />
                  <Form.Control.Feedback type="invalid">
                    Last name is required.
                  </Form.Control.Feedback>
                </Form.Group>
              </Col>
            </Row>

            <Row>
              <Col xs={12} md={6}>
                <Form.Group className="mb-3" controlId="dob">
                  <Form.Label>Date of Birth <span className="text-muted">(optional)</span></Form.Label>
                  <Form.Control
                    type="date"
                    value={dob}
                    onChange={(e) => setDob(e.target.value)}
                  />
                </Form.Group>
              </Col>

              <Col xs={12} md={6}>
                <Form.Group className="mb-3" controlId="weight">
                  <Form.Label>Body Weight (lbs) <span className="text-muted">(optional)</span></Form.Label>
                  <Form.Control
                    type="number"
                    min={1}
                    max={500}
                    placeholder="e.g. 170"
                    value={weight}
                    onChange={(e) => setWeight(e.target.value)}
                    isInvalid={validated && weight && (isNaN(+weight) || +weight < 1 || +weight > 500)}
                  />
                  <Form.Control.Feedback type="invalid">
                    Weight must be between 1 and 500 lbs.
                  </Form.Control.Feedback>
                </Form.Group>
              </Col>
            </Row>

            <Form.Group className="mb-3" controlId="password">
              <Form.Label>New Password <span className="text-muted">(leave blank to keep current)</span></Form.Label>
              <Form.Control
                type="password"
                placeholder="********"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                isInvalid={validated && password.trim().length > 0 && password.length < 8}
              />
              <Form.Control.Feedback type="invalid">
                Password must be at least 8 characters.
              </Form.Control.Feedback>
            </Form.Group>

            <div className="d-flex justify-content-between align-items-center mt-3">
              <Button type="submit" variant="maroon" disabled={submitting}>
                {submitting ? "Saving..." : "Save Changes"}
              </Button>

              <Button
                type="button"
                variant="outline-dark"
                disabled={submitting}
                onClick={() => navigate("/dashboard")}
              >
                Back to Dashboard
              </Button>
            </div>
          </Form>
        </Card.Body>
      </Card>
    </div>
  );
}