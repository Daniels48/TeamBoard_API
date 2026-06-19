async function sendResetCode(){

    const email =document.getElementById("email").value.trim()
    if(!email){
        alert("Enter email")
        return
    }

    const btn =document.getElementById("send-btn")

    btn.disabled = true
    btn.textContent = "Sending..."

    const res = await window.api.post("/api/auth/forgot-password", {email})

    if(!res.ok){
        btn.disabled = false
        btn.textContent = "Send Code"
        alert("Failed to send code")
        return
    }
    document.getElementById("verify-block").classList.remove("hidden")
    btn.textContent ="Code Sent ✓"
}



async function verifyResetCode(){
    const email =document.getElementById("email").value.trim()
    const code =document.getElementById("code").value.trim()

    if(!code){
        alert("Enter verification code")
        return
    }

    const res = await window.api.post("/api/auth/verify-reset-code", {email, code})

    if(!res.ok){
        alert("Invalid code")
        return
    }
    const result = await res.json()
    window.location.href =`/reset-password?token=${encodeURIComponent(result.reset_token)}`;
}