import { Container } from "react-bootstrap";
import { Outlet } from "react-router-dom";
import AppNav from "./AppNav";
import AppFooter from "./AppFooter";

export default function Layout() {

    // This layout route in specific/particular makes use of my Navbar and Footer components to render them for every page
    return (
        <div className="app-shell">
            <AppNav />
            <main className="app-main">
                <Container style={{ paddingTop: 16, paddingBottom: 24 }}>
                    <Outlet />
                </Container>
            </main>
            <AppFooter />
        </div>
    );
}