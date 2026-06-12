const token = localStorage.getItem("access_token")

if(!token){
    window.location.href="/static/login.html"
}

async function loadProfile(){
    const res = await window.api.get("/api/users/me")

    if(res.status===401){
        window.location.href="/static/login.html"
        return
    }

    const user = await res.json()

    document.getElementById("username").innerText =user.username
    document.getElementById("email").innerText =user.email
    document.getElementById("role").innerText =user.role
    const created = new Date(user.created_at)
    document.getElementById("created").textContent = created.toLocaleString()

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

function logout(){
    localStorage.removeItem("access_token")
    window.api.post("/api/auth/logout")
    window.location.href="/"
}

function goBoards(){
    window.location.href="/static/boards.html"
}


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

loadProfile()
