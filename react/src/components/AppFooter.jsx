import { Container } from "react-bootstrap";

export default function AppFooter() {
    
    // This entire function/Component just returns a simple Footer with copyright notice
    return (
        <footer className="footer-bar">
            <Container className="text-center small">
                © ShreddedNerds {new Date().getFullYear()}
            </Container>
        </footer>
    );
}