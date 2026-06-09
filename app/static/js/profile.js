const token = localStorage.getItem("access_token")

if(!token){
    window.location.href="/static/login.html"
}

async function loadProfile(){

    const res = await fetch("/api/users/me",{
        headers:{
            "Authorization":"Bearer "+token
        }
    })

    if(res.status===401){
        window.location.href="/static/login.html"
        return
    }

    const user = await res.json()

    document.getElementById("username").innerText =
        user.username

    document.getElementById("email").innerText =
        user.email

    document.getElementById("role").innerText =
        user.role

    document.getElementById("created").innerText =
        user.created_at

    const status =
        document.getElementById(
            "verification-status"
        )

    const block =
        document.getElementById(
            "verification-block"
        )

    if(user.is_verified){

        status.textContent =
            "Verified ✅"

        block.style.display =
            "none"
    }
    else{

        status.textContent =
            "Not Verified ❌"
    }
}

function logout(){

    localStorage.removeItem("access_token")

    fetch("/api/auth/logout",{
        method:"POST",
        credentials:"include"
    })

    window.location.href="/"
}

function goBoards(){
    window.location.href="/static/boards.html"
}


async function verifyEmail(){

    const code =
        document.getElementById(
            "verification-code"
        ).value.trim()

    if(!code){
        alert("Enter verification code")
        return
    }

    const res =
        await apiFetch(
            "/api/auth/verify-email",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                    "application/json"
                },
                body: JSON.stringify({
                    code
                })
            }
        )

    if(!res || !res.ok){
        alert("Invalid code")
        return
    }

    document.getElementById(
        "verification-status"
    ).textContent =
        "Verified ✅"

    document.getElementById(
        "verification-block"
    ).style.display =
        "none"

    alert("Email verified")
}


async function sendVerificationEmail(){

    const btn =
        document.getElementById(
            "verify-email-btn"
        )

    btn.disabled = true
    btn.textContent = "Sending..."

    const res =
        await apiFetch(
            "/api/auth/send-verification-email",
            {
                method:"POST"
            }
        )

    if(!res || !res.ok){

        btn.disabled = false
        btn.textContent = "Verify Email"

        alert(
            "Failed to send email"
        )

        return
    }

    btn.textContent =
        "Email Sent ✓"
}

loadProfile()
