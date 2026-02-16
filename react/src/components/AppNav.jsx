import { useEffect, useState } from "react";
import { Container, Navbar, Nav, NavDropdown, Button } from "react-bootstrap";
import { NavLink, useNavigate, useLocation } from "react-router-dom";
import { api } from "../api";

export default function AppNav() {

    // Variable to track whether user is authenticated or not
    const [me, setMe] = useState(null);
    const navigate = useNavigate();
    const location = useLocation();

    // This part just does a minimal session check
    // THis is the 'side effect' part of this component and function
    // It calls the backend path of /auth/status to verify if user has authenticated or not and stores the same info in the me variable
    useEffect(() => {
        api("/auth/status")
        .then((resp) => setMe(resp?.user || null))
        .catch(() => setMe(null));
    }, [location.pathname]);

    const handleLogout = async () => {
        try {
            await api("/auth/logout", { method: "POST" });
        } finally {
            setMe(null);
            navigate("/login");
        }
    };

    return (
        <Navbar expand="lg" className="navbar-shr" sticky="top">
            <Container>

                {/* In this area I am just creating the brand logo for my site and the name */}
                <Navbar.Brand as={NavLink} to="/">
                    <img src="/shredded-nerds-logo.png" alt="ShreddedNerds Logo" width="32" height="32" className="me-2" onError={(e) => (e.currentTarget.style.display = 'none')} />
                    <span>ShreddedNerds</span>
                </Navbar.Brand>

                <Navbar.Toggle aria-controls="main-nav" />
                <Navbar.Collapse id="main-nav">
                    {/* This is the left side of the Navbar which will contain the main links / most important tabs */}
                    <Nav className="me-auto">
                        <Nav.Link as={NavLink} to="/dashboard">Dashboard</Nav.Link>
                        <Nav.Link as={NavLink} to="/classes">All Classes</Nav.Link>
                        <Nav.Link as={NavLink} to="/leaderboards">Leaderboards</Nav.Link>
                        <Nav.Link as={NavLink} to="/personal-records">My PRs</Nav.Link>
                        <Nav.Link as={NavLink} to="/schedule">Schedule</Nav.Link>
                        <Nav.Link as={NavLink} to="/workouts">Log Workouts</Nav.Link>
                    </Nav>

                    {/* This side would contain additional pages/links and Auth pages*/}
                    <Nav className="ms-auto align-items-center">
                        <NavDropdown title="More" id="more-dd" align="end">
                        <NavDropdown.Divider />
                        <NavDropdown.Item as={NavLink} to="/about">About</NavDropdown.Item>
                        </NavDropdown>

                        {!me ? (
                            <>
                                <Nav.Link as={NavLink} to="/login" className="ms-2">Login</Nav.Link>
                                <Button className="ms-2 btn-outline-maroon" onClick={() => navigate("/register")} variant="outline-dark">Sign Up</Button>
                            </>
                            ) : (
                            <>
                                {/* If the user is logged in/user exists then the navbar will make note of their username/login status */}
                                <Navbar.Text className="ms-3 me-2">Signed in as <strong>{me.Username}</strong></Navbar.Text>
                                <Button variant="outline-dark" className="me-2" onClick={() => navigate("/profile")} sz="sm">Profile</Button>
                                <Button variant="outline-dark" onClick={handleLogout}>Log out</Button>
                            </>
                        )}
                    </Nav>
                </Navbar.Collapse>
            </Container>
        </Navbar>
    );
}

