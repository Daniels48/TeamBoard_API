const token = localStorage.getItem("access_token")
const URL_SESSIONS = "/api/auth/sessions";
const URL_LOGOUT_ALL = "/api/auth/logout-all";

if(!token){
    window.location.href="/login"
}

async function loadProfile(){
    const res = await window.api.get("/api/users/me")

    if(res.status===401){
        window.location.href="/login"
        return
    }

    const user = await res.json()

    document.getElementById("username").innerText =user.username
    document.getElementById("email").innerText =user.email
    document.getElementById("role").innerText =user.role
    document.getElementById("f_name").innerText =user.first_name
    document.getElementById("l_name").innerText =user.last_name
    const created = new Date(user.created_at)
    document.getElementById("created").textContent = formatUpdated(user.created_at)

    const status =document.getElementById("verification-status")
    const block =document.getElementById("verification-block")

    if(user.is_verified){
        status.textContent ="Verified ✅"
        block.style.display ="none"
    }
    else{
        status.textContent ="Not Verified ❌"
    }
}

async function logout() {
    const button = document.getElementById("logout-btn");

    try {
        button.disabled = true;
        button.textContent = "Logging out...";

        await window.api.post("/api/auth/logout");

        localStorage.removeItem("access_token");

        window.location.href = "/login";
    } catch (error) {
        console.error("Logout failed:", error);

        button.disabled = false;
        button.textContent = "Log out";

        alert("Could not log out. Please try again.");
    }
}

function goBoards(){window.location.href="/boards"}


async function verifyEmail(){
    const code =document.getElementById("verification-code").value.trim()

    if(!code){
        alert("Enter verification code")
        return
    }

    const res = await window.api.post("/api/auth/verify-email", {code})

    if(!res || !res.ok){
        alert("Invalid code")
        return
    }

    document.getElementById("verification-status").textContent ="Verified ✅"
    document.getElementById("verification-block").style.display ="none"
    alert("Email verified")
}


async function sendVerificationEmail(){
    const btn = document.getElementById("verify-email-btn")
    btn.disabled = true
    btn.textContent = "Sending..."

    const res = await window.api.post("/api/auth/send-verification-email")

    if(!res || !res.ok){
        btn.disabled = false
        btn.textContent = "Verify Email"
        alert("Failed to send email")
        return
    }
    btn.textContent ="Email Sent ✓"
}

function formatUpdated(dateString) {
    const date = new Date(dateString);
    const now = new Date();

    let text = "";

    const diffMs = now - date;
    const diffMinutes = Math.floor(diffMs / 1000 / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMinutes < 1) return `${text} just now`;
    if (diffMinutes < 60) return `${text} ${diffMinutes}m ago`;
    if (diffHours < 24) return `${text} ${diffHours}h ago`;
    if (diffDays === 1) return `${text} yesterday`;
    if (diffDays < 30) return `${text} ${diffDays} days ago`;

    return `${text} ${date.toLocaleDateString()}`;
}


function getDeviceIcon(session) {
    const deviceType = (session.device_type || "").toLowerCase();
    const os = (session.os || "").toLowerCase();

    if (
        deviceType.includes("mobile") ||
        deviceType.includes("phone") ||
        os.includes("android") ||
        os.includes("ios")
    ) {
        return "📱";
    }

    if (
        deviceType.includes("tablet") ||
        os.includes("ipad")
    ) {
        return "📲";
    }

    return "💻";
}

async function loadSessions() {
    const container = document.getElementById("sessions-list");

    if (!container) return;

    container.textContent = "Loading sessions...";

    try {
        const res = await window.api.get(URL_SESSIONS);

        if (!res || !res.ok) {
            container.textContent = "Could not load sessions";
            return;
        }

        const sessions = await res.json();

        if (!sessions.length) {
            container.textContent = "No active sessions";
            return;
        }

        container.innerHTML = sessions.map(session => {
            const device = [session.browser, session.os].filter(Boolean).join(" on ") || "Unknown device";
            const browser = session.browser || "";
            const os = session.os || "";
            const ip = session.ip_address || "";
            const icon = getDeviceIcon(session);
            const lastUsed = session.last_used_at || "";

            return `
                <div class="session-item">
                    <div class="session-main">
                        <div class="session-icon">${getDeviceIcon(session)}</div>

                        <div class="session-info">
                            <strong>${device}</strong>
                            <p>IP address: ${session.ip_address || "Unknown"}</p>
                            <p>Last active: ${formatUpdated(lastUsed)}</p>
                        </div>
                    </div>

                    <button class="session-logout-btn"type="button"onclick="logoutDevice('${session.session_id}')">Log out</button>
                </div>
            `;
        }).join("");

    } catch (error) {
        console.error("Failed to load sessions:", error);
        container.textContent = "Could not load sessions";
    }
}

async function logoutDevice(sessionId) {
    try {
        const res = await window.api.del(
            `/api/auth/sessions/${sessionId}`,
        );
        console.log("logoutDevice response:", res);
        console.log("status:", res?.status);
        if (!res || !res.ok) {
            alert("Could not log out this device");
            return;
        }

        await loadSessions();

    } catch (error) {
        console.error("Failed to logout device:", error);
        alert("Could not log out this device");
    }
}

async function logoutAllSessions() {
    const confirmed = window.confirm(
        "Log out from all devices?",
    );

    if (!confirmed) return;

    try {
        const res = await window.api.post(URL_LOGOUT_ALL);

        if (!res || !res.ok) {
            alert("Could not log out from all devices");
            return;
        }

        window.clearToken();
        window.currentUser = null;

        window.location.href = "/login";

    } catch (error) {
        console.error("Failed to logout all sessions:", error);
        alert("Could not log out from all devices");
    }
}



async function updateProfile() {
    const URL_UPDATE_PROFILE = "/api/users/profile";
    const currentEmail = document.getElementById("email").textContent;
    const current_firstName = document.getElementById("f_name").textContent;
    const current_lastName = document.getElementById("l_name").textContent;

    const email = prompt("Enter new email:", currentEmail);
    if (email === null) return; // cancel

    const firstName = prompt("Enter new first name:", current_firstName);
        if (firstName === null) return; // cancel

    const lastName = prompt("Enter new last name:", current_lastName);
        if (lastName === null) return; // cancel

    const payload = {
        email: email.trim(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
    };

    try {
        const res = await window.api.put(URL_UPDATE_PROFILE, payload);

        if (!res || !res.ok) {
            const err = await res?.text();
            console.error(err);
            alert("Failed to update profile");
            return;
        }

        const data = await res.json();

        document.getElementById("email").textContent = data.email;
        document.getElementById("f_name").textContent = data.first_name;
        document.getElementById("l_name").textContent = data.last_name;

        alert("Profile updated successfully");

    } catch (e) {
        console.error("Update profile error:", e);
        alert("Something went wrong");
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    await loadProfile();
    await loadSessions();
});

