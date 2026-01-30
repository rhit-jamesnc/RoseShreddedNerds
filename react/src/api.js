// This is a helper JS file to handle cookies and sessions
// The code in this file will ensure that every request automatically includes JSON headers, session cookies, and consistent error shape

const BASE = import.meta.env.VITE_API_BASE || "/api";
console.log("API BASE =", BASE);

export async function api(path, { method = "GET", body } = {}) {
    console.log("API BASE =", BASE);
    const opts = {
        method,
        headers: {"Content-Type": "application/json" },
        credentials: "include", // Send/receive Flask session cookie
    };

    if (body) {
        opts.body = JSON.stringify(body);
    }

    const resp = await fetch(`${BASE}${path}`, opts);
    let data = null;
    try {
        data = await resp.json();
    }
    catch { /* No body */ }

    if (!resp.ok) {
        throw new Error(data?.error || `HTTP ${resp.status}`);
    }
    return data;
}
