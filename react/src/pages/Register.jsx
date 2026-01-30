
import { useState } from "react";
import { useNavigate, NavLink } from "react-router-dom";
import { Form, Button, Card, Alert, Row, Col } from "react-bootstrap";
import { api } from "../api";


export default function Register() {

  const navigate = useNavigate();

  // These are the form fields for the Registration form
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  // These are variables which store the UI state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  // The side effects method/function which essentially gets the form data via api call
  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setInfo("");

    // This is some basic client-side validation which I have added. There is seperate server side validation too
    if (!firstName.trim() || !lastName.trim()) {
      setError("Please enter your first and last name.");
      return;
    }
    if (!username.trim()) {
      setError("Please enter a username.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
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
      };

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

            {/* Making the form using grid/column layout sucht hat first name and last name field appear in same row */}
            <Row>
              <Col xs={12} md={6}>
                <Form.Group className="mb-3" controlId="firstName">
                  <Form.Label>First name</Form.Label>
                  <Form.Control type="text" placeholder="John" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
                </Form.Group>
              </Col>

              <Col xs={12} md={6}>
                <Form.Group className="mb-3" controlId="lastName">
                  <Form.Label>Last name</Form.Label>
                  <Form.Control type="text" placeholder="Snow" value={lastName} onChange={(e) => setLastName(e.target.value)} />
                </Form.Group>
              </Col>
            </Row>

            <Form.Group className="mb-3" controlId="username">
              <Form.Label>Username</Form.Label>
              <Form.Control type="text" placeholder="johnsnow" value={username} onChange={(e) => setUsername(e.target.value)} />
              <Form.Text className="text-muted">
                Username must start with a letter and be 3-20 characters in length, and may contain letters, numbers, hyphen, and underscore only.
              </Form.Text>
            </Form.Group>

            <Form.Group className="mb-3" controlId="password">
              <Form.Label>Password</Form.Label>
              <Form.Control type="password" placeholder="j0hn-sn0w123" value={password} onChange={(e) => setPassword(e.target.value)} />
            </Form.Group>

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
