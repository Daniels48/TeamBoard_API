async function resetPassword(){
    const params = new URLSearchParams(window.location.search)
    const token = params.get("token")

    if (!token) {
        alert("Reset token is missing");
        window.location.href = "/";
        return;

    }
    const password =document.getElementById("new-password").value
    const confirm =document.getElementById("confirm-password").value
    const error =document.getElementById("error")
    error.textContent = ""
    if(password !== confirm){
        error.textContent = "Passwords do not match"
        return
    }

    const res = await window.api.post("/api/auth/reset-password", {token, new_password: password})

    if(!res.ok){
        error.textContent ="Failed to reset password"
        return
    }

    alert("Password changed successfully")
    window.location.href ="/login"
}


