async function login(){
    const loginValue = document.getElementById("login").value.trim()
    const password = document.getElementById("password").value
    const errorEl = document.getElementById("error")
    errorEl.innerText = ""
    try{
        const res = await window.api.post("/api/auth/login", {login:loginValue,password:password})

        if(!res.ok){
            const error =await res.json()
            errorEl.innerText =error.detail || "Login failed"
            return
        }

        const data = await res.json()
        window.setToken(data.access_token)

        window.location.href="/"

    }catch(e){
        console.error(e)
        errorEl.innerText ="Server unavailable"
    }
}