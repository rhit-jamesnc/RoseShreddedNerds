import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";

// Importing all pages directly from the src/pages folder
import Home from "./pages/Home.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Leaderboards from "./pages/Leaderboards.jsx";
import Schedule from "./pages/Schedule.jsx";
import Workouts from "./pages/Workouts.jsx";
import About from "./pages/About.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import PersonalRecords from "./pages/PersonalRecords.jsx";
import ClassList from "./pages/ClassList.jsx";

// Simple function to render a basic 404 not found page
function NotFound() {
  return (
    <div className="text-center py-5">
      <h2>404</h2>
      <p>Page not found.</p>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>

        {/* One thing to note here is that all pages inside Layout will automatically get Navbar and Footer */}
        <Route element={<Layout />}>

          {/* This is the Home/default route */}
          <Route index element={<Home />} />

          {/* These are the most important routes which match my navbar links */}
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="classes" element={<ClassList />} />
          <Route path="leaderboards" element={<Leaderboards />} />
          <Route path="personal-records" element={<PersonalRecords />} />
          <Route path="schedule" element={<Schedule />} />
          <Route path="workouts" element={<Workouts />} />

          {/* these are the other pages of my web-app */}
          <Route path="about" element={<About />} />

          {/* Authentication Routes */}
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />

          <Route path="home" element={<Navigate to="/" replace/>} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}