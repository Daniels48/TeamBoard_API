const TOKEN_KEY = "access_token"
const TEXT_CODE = "Token expired";
let refreshPromise = null
let accessToken = localStorage.getItem(TOKEN_KEY)
let currentUser = null

function setToken(token) {
    accessToken = token
    localStorage.setItem(TOKEN_KEY, token)
}

function clearToken() {
    accessToken = null
    localStorage.removeItem(TOKEN_KEY)
}

async function refreshToken(){
    if(refreshPromise){
        return refreshPromise
    }
    refreshPromise=(async()=>{
        const res = await fetch(
            "/api/auth/refresh",
            {
                method:"POST",
                credentials:"include"
            }
        )
        if(!res.ok){
            clearToken()
            return false
        }
        const data = await res.json()
        setToken(data.access_token)
        return true
    })()

    try{
        return await refreshPromise
    }finally{
        refreshPromise = null
    }
}

async function request(url, options={}){
    const headers = {...(options.headers || {})}

    if(accessToken){headers.Authorization = `Bearer ${accessToken}`}

    return fetch(url,
        {
            ...options,
            headers,
            credentials:"include"
        }
    )
}

async function apiFetch(url, options={}){
    let res = await request(url,options)

    if(res.status!==401){return res}
    let error = null
    try{
        error = await res.json()
    }catch{
        return res
    }
    if(error.error!==TEXT_CODE){
        return res
    }

    const refreshed = await refreshToken()

    if(!refreshed){
        clearToken()
        currentUser = null
        window.location.href = "/static/login.html"
        return null
    }

    return request(url, options)
}

async function initAuth(){

    try{
        const url_check = "/api/users/check";
        const res = await apiFetch(url_check);
        if(res && res.ok){currentUser = await res.json()}

    }catch(e){

        console.error(
            "Auth init error:",
            e
        )

    }

    renderNavbar()

}

function renderNavbar(){

    const container = document.getElementById("nav-buttons")

    if(!container){
        return
    }

    if(!currentUser){

        container.innerHTML = `
            <button class="login" onclick="goLogin()">Login</button>
            <button class="register" onclick="goRegister()">Register</button>
        `

    }else{

        container.innerHTML = `
            <span class="user">👤 ${currentUser.username}</span>
            <button class="boards" onclick="goBoards()">My Boards</button>
            <button class="profile" onclick="goProfile()">Profile</button>
            <button class="logout" onclick="logout()">Logout</button>
        `
    }
}

function goLogin(){
    window.location.href = "/static/login.html"
}

function goRegister(){
    window.location.href = "/static/register.html"
}

function goBoards(){
    window.location.href = "/static/boards.html"
}

function goProfile(){
    window.location.href = "/static/profile.html"
}


async function logout(){

    try{
        await fetch(
            "/api/auth/logout",
            {
                method:"POST",
                credentials:"include"
            }
        )
    }catch(e){
        console.error(e)
    }
    clearToken()
    currentUser = null
    renderNavbar()
    window.location.href =
        "/static/index.html"
}

document.addEventListener(
    "DOMContentLoaded",
    initAuth
)
