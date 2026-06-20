const URL_check = "/api/users/check";
const url_logout = "/api/auth/logout";
const url_index = "/";
const url_board = "/boards";
const url_register = "/register";
const url_login = "/login";
const url_profile = "/profile";



async function initAuth(){

    try{
        const res = await window.api.get(URL_check);
        if(res && res.ok){
        window.currentUser = await res.json()
        }

    }catch(e){
        console.error("Auth init error:", e)
    }
    renderNavbar()
}

function renderNavbar(){
    const container = document.getElementById("nav-buttons")
    if(!container){return}
    if(!window.currentUser){
        container.innerHTML = `
            <button class="login" onclick="goLogin()">Login</button>
            <button class="register" onclick="goRegister()">Register</button>
        `
    }else{
        container.innerHTML = `
            <span class="user">👤 ${window.currentUser.username}</span>
            <button class="boards" onclick="goBoards()">My Boards</button>
            <button class="profile" onclick="goProfile()">Profile</button>
            <button class="logout" onclick="logout()">Logout</button>
        `
    }
}

function goLogin(){window.location.href = url_login}

function goRegister(){window.location.href = url_register}

function goBoards(){window.location.href = url_board}

function goProfile(){window.location.href = url_profile}

async function logout(){
    const button = document.querySelector(".logout");

    try {
        button.disabled = true;
        button.textContent = "Logging out...";

        await window.api.post(url_logout);

        localStorage.removeItem("access_token");

        window.clearToken()
        window.currentUser = null
        renderNavbar()

        window.location.href = url_login;
    } catch (error) {
        console.error("Logout failed:", error);
        button.disabled = false;
        button.textContent = "Log out";
        alert("Could not log out. Please try again.");
    }

}


async function verifyEmail(){

    const code = document.getElementById("verification-code").value.trim()

    if(!code){alert("Enter verification code"); return}

    const url_verify_email = "/api/auth/verify-email"

    const res = await window.api.post(url_verify_email, {code})

    if(!res || !res.ok){
        alert("Invalid code")
        return
    }

    document.getElementById("verification-status").textContent = "Verified ✅"
    document.getElementById("verification-block").style.display ="none"
    alert("Email verified")
}

document.addEventListener("DOMContentLoaded",initAuth)
