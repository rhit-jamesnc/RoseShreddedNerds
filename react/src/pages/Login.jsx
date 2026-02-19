import { useState } from "react";
import { useNavigate, NavLink } from "react-router-dom";
import { Form, Button, Card, Alert } from "react-bootstrap";
import { api } from "../api";


export default function Login() {

  const navigate = useNavigate();

  // These are the form fields
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  // These track the state of the user interface itself
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const [validated, setValidated] = useState(false);

  // The side effect function
  // Just like most of the pages, this too just makes api call to fetch the actual data and fields sitself
  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setInfo("");
    setValidated(true);

    if(!username.trim() || !password.trim()) {
      setError("Please fill in all required fields.");
      return;
    }

    setSubmitting(true);

    // We define the request payload which includes the username and password, we send request to API
    // If everything went fine, we set success message, otherwise we catch error, and set state of submittin form to false
    try {
      const payload = {
        username: username.trim(),
        password: password.trim(),
      };

      const resp = await api("/auth/login", {
        method: "POST",
        body: payload,
      });

      if (resp && resp.user) {
        setInfo("Welcome back! Redirecting to your dashboard...");
      }

      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Login failed. Please check the credentials.");
    } finally {
      setSubmitting(false);
    }

  }

  return (
    <div className="auth-page">
      <Card className="auth-card shadow-sm">
        <Card.Body>

          <h2 className="mb-1">Welcome Back!</h2>
          <p className="text-muted mb-3 small">
            We missed you but glad you're back on the grind!
          </p>

          {/* This is just the common area/space I have dedicated to display success or error message */}
          {error && (<Alert variant="danger" className="py-2">{error}</Alert>)}
          {info &&  (<Alert variant="success" className="py-2">{info}</Alert>)}

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
            </Form.Group>

            <Form.Group className="mb-3" controlId="password">
              <Form.Label>Password</Form.Label>
              <Form.Control
                type="password"
                placeholder="j0hn-sn0w123"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                isInvalid={validated && !password.trim()}
              />
              <Form.Control.Feedback type="invalid">
                Password is required.
              </Form.Control.Feedback>
            </Form.Group>


            <div className="d-flex justify-content-between align-items-center mt-3">
              {/* This conditionally renders logging in message vs the button itself based on whether our form is getting submitted or not */}
              <Button type="submit" variant="maroon" disabled={submitting}>{submitting ? "Logging in..." : "Log in"}</Button>
              <div className="small text-muted">
                Don't have an account? {""}
                <NavLink to="/register">Sign up</NavLink>
              </div>
            </div>
          </Form>
        </Card.Body>
      </Card>
    </div>
  );
}