"use strict";
const TEXT_CODE = "Token expired";
const URL_REFRESH = "/api/auth/refresh";
const URL_LOGIN = "/static/login.html";
const TOKEN_KEY = "access_token";
window.currentUser = null;
let refreshPromise = null;
let accessToken = localStorage.getItem(TOKEN_KEY);


function setToken(token) {
    accessToken = token
    localStorage.setItem(TOKEN_KEY, token)
}

function clearToken() {
    accessToken = null
    localStorage.removeItem(TOKEN_KEY)
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
    if(res.status!==401){
        return res
    } else {
         let error = null
        try{error = await res.json()}
        catch{
            return res
        }
        if(error.error!==TEXT_CODE){
            return res
        }

        const refreshed = await refreshToken()

        if(!refreshed){
            window.clearToken()
            window.currentUser = null
            window.location.href = URL_LOGIN;
            return null
        }

        return request(url, options)
    }
}

const jsonOptions = (method, data = null) => ({
    method,
    headers: {
        "Content-Type": "application/json"
    },
    ...(data !== null && {
        body: JSON.stringify(data)
    })
})

const api = {
    get: (url) => apiFetch(url),

    post: (url, data) => apiFetch(url, jsonOptions("POST", data)),

    patch: (url, data) => apiFetch(url, jsonOptions("PATCH", data)),

    del: (url) => apiFetch(url, {method: "DELETE"}),
}

async function refreshToken(){
    if(refreshPromise){
        return refreshPromise
    }
    refreshPromise=(async()=>{
        const res = await fetch(URL_REFRESH, {method: "POST", credentials: "include"})
        if(!res.ok){
            window.clearToken()
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

window.api = api
window.clearToken = clearToken
window.setToken = setToken