
import { useState } from "react";
import { useNavigate, NavLink } from "react-router-dom";
import { Form, Button, Card, Alert, Row, Col } from "react-bootstrap";
import { api } from "../api";

const USERNAME_RE = /^[a-zA-Z][a-zA-Z0-9_-]{2,19}$/;

export default function Register() {

  const navigate = useNavigate();

  // These are the form fields for the Registration form
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [dob, setDob] = useState("");
  const [weight, setWeight] = useState("");
  const [role, setRole] = useState("student");

  // These are variables which store the UI state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const [validated, setValidated] = useState(false);

  // The side effects method/function which essentially gets the form data via api call
  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setInfo("");
    setValidated(true);

    // This is some basic client-side validation which I have added. There is seperate server side validation too
    if (!firstName.trim() || !lastName.trim()) {
      setError("Please enter your first and last name.");
      return;
    }
    if (!username.trim()) {
      setError("Please enter a username.");
      return;
    }
    if (!USERNAME_RE.test(username.trim())) {
      setError("Username must start with a letter, be 3-20 characters, and contain only letters, numbers, hyphens, or underscores.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (weight && (isNaN(+weight) || +weight < 1 || +weight > 500)) {
      setError("Weight must be a number between 1 and 500 lbs.");
      return;
    }

    // If none of the code in above conditions was executed, it means on a basic level registration entries are valid
    setSubmitting(true);
    try {
      
      // Defining the payload that will be sent as part of the body of the post request
      const payload = {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        username: username.trim(),
        password: password,
        role: role,
      };

      if (dob) payload.dob = dob;
      if (weight) payload.weight = Number(weight);

      // The actual api call to the backend route for registeration
      // I am passing in the above defined payload as the body
      const resp = await api("/auth/register", {
        method: "POST",
        body: payload,
      });

      // If everything is successfull and I actually get a user, I set the success message as account created, otherwise 
      if (resp && resp.user) {
        setInfo("Account created! Redirecting to the Dashboard");
        navigate("/dashboard");
      } 
      else {
        navigate("/dashboard");
      }
    } catch (err) {
      setError(err.message || "There was an error with Registration.");
    } finally {
      setSubmitting(false);
    }

  }

  return (
    <div className="auth-page">
      <Card className="auth-card shadow-sm">
        <Card.Body>
          <h2 className="mb-1">Create an Account</h2>
          <p className="text-muted mb-3 small">Join the pack! Smarter Lifts = Stronger Campus.</p>

          {error && (<Alert variant="danger" className="py-2">{error}</Alert>)}
          {info && (<Alert variant="success" className="py-2">{info}</Alert>)}

          <Form onSubmit={handleSubmit} autoComplete="off">

            <Form.Group className="mb-4">
              <Form.Label className="d-block">I am a...</Form.Label>
              <div className="d-flex gap-4">
                <Form.Check
                  type="radio"
                  label="Student"
                  name="roleGroup"
                  id="roleStudent"
                  checked={role === "student"}
                  onChange={() => setRole("student")}
                />
                <Form.Check
                  type="radio"
                  label="Trainer"
                  name="roleGroup"
                  id="roleTrainer"
                  checked={role === "trainer"}
                  onChange={() => setRole("trainer")}
                />
              </div>
              <Form.Text className="text-muted">
                {role === "trainer" 
                  ? "Trainers can create classes and manage schedules." 
                  : "Students can log workouts and join trainer-led classes."}
              </Form.Text>
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

            <Form.Group className="mb-3" controlId="username">
              <Form.Label>Username</Form.Label>
              <Form.Control
                type="text"
                placeholder="smth"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                isInvalid={validated && (!username.trim() || !USERNAME_RE.test(username.trim()))}
              />
              <Form.Control.Feedback type="invalid">
                {!username.trim()
                  ? "Username is required."
                  : "Must start with a letter, 3-20 characters, letters/numbers/hyphens/underscores only."}
              </Form.Control.Feedback>
              {!(validated && (!username.trim() || !USERNAME_RE.test(username.trim()))) && (
                <Form.Text className="text-muted">
                  Username must start with a letter and be 3-20 characters in length, and may contain letters, numbers, hyphen, and underscore only.
                </Form.Text>
              )}
            </Form.Group>

            <Form.Group className="mb-3" controlId="password">
              <Form.Label>Password</Form.Label>
              <Form.Control
                type="password"
                placeholder="j0hn-sn0w123"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                isInvalid={validated && password.length < 8}
              />
              <Form.Control.Feedback type="invalid">
                Password must be at least 8 characters.
              </Form.Control.Feedback>
            </Form.Group>

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

            <div className="d-flex justify-content-between align-items-center mt-3">
              {/* This is another instance of rendering part conditionally */}
              <Button type="submit" variant="maroon" disabled={submitting}>{submitting ? "Creating account..." : "Sign up"}</Button>

              <div className="small text-muted">
                Already have an account? {""}
                <NavLink to="/login">Log in</NavLink>
              </div>
            </div>
          </Form>
        </Card.Body>
      </Card>
    </div>
  );
}