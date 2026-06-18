"use strict";

async function register(){
    const error =document.getElementById("error");
    error.innerText = "";
    const body = {
        username:document.getElementById("username").value.trim(),
        email:document.getElementById("email").value.trim(),
        password:document.getElementById("password").value,
        first_name:document.getElementById("first_name").value.trim(),
        last_name:document.getElementById("last_name").value.trim()
    };

     if(!body.username){
        error.innerText = "Username is required";
        return;
     }

    if(!body.email){
        error.innerText = "Email is required";
        return;
    }

    if(!body.email.includes("@")){
        error.innerText ="Invalid email";
        return;
    }

    if(!body.password){
        error.innerText ="Password is required";
        return;
    }

    if(body.password.length < 8){
        error.innerText ="Password must be at least 8 characters";
        return;
    }

    try{
        const res = await window.api.post("/api/auth/register",body);

        if(!res || !res.ok){
            let message ="Registration failed";

            try{
                const data =await res.json();
                if(data.detail){message = data.detail;}
            }catch{}
            error.innerText =message;
            return;
        }
        alert("Registration successful");
        window.location.href ="/static/login.html";

    }catch(e){
        console.error(e);
        error.innerText ="Server error";
    }
}