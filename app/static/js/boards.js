async function loadBoards() {
    const container = document.getElementById("boards")
    container.innerHTML = "Loading..."
    const res = await window.api.get("/api/boards");

    if(!res){return}

    if(!res.ok){
        container.innerHTML ="Ошибка загрузки"
        return
    }

    const boards = await res.json()
    renderBoards(boards)
}


function renderBoards(boards){
    const container = document.getElementById("boards")
    container.innerHTML = ""
    if(boards.length === 0){
        container.innerHTML ="Нет доступных досок"
        return
    }

    boards.forEach(board => {
        const div = document.createElement("div")
        div.className = "board"
        div.innerHTML = `
        <h3>${board.title}</h3>
        <p>
            ${board.description || "No description"}
        </p>
        <div class="board-footer">
            <span>
                ${new Date(board.created_at)
                    .toLocaleDateString()}
            </span>

            <span class="${
                board.is_public
                ? "public"
                : "private"
            }">
                ${
                    board.is_public
                    ? "🌍 Public"
                    : "🔒 Private"
                }
            </span>
        </div>
        `
        div.onclick = () => {window.location.href =`/static/board.html?id=${board.public_id}`}

        container.appendChild(div)
    })
}


async function createBoard(){
    const title = document.getElementById("title").value.trim()
    const description = document.getElementById("description").value.trim()
    const isPublic = document.getElementById("is_public").checked

    if(!title){
        alert("Введите название")
        return
    }

    const url_boards = "/api/boards"
    const res = await window.api.post(url_boards, {title,description,is_public:isPublic})

    if(!res || !res.ok){
        alert("Ошибка создания доски")
        return
    }

    document.getElementById("title").value = ""
    document.getElementById("description").value = ""
    document.getElementById("is_public").checked = false

    await loadBoards()
}


function renderRole(){

    if(!currentUser){
        console.log("331ss")
        return
    }

    const userInfo =document.getElementById("user-info")

    const boardsTitle =document.getElementById( "boards-title")

    userInfo.innerHTML = `
        <div>👤 ${currentUser.username}</div>
        <div>Role:${currentUser.role}</div>
    `

    if(
        currentUser.role === "ADMIN"
    ){
        boardsTitle.textContent = "All Boards"
    }else{
        boardsTitle.textContent = "My Boards"
    }
}


async function initBoards(){

    try{
        const res = await window.api.get("/api/users/check");
        if(res && res.ok){
            window.currentUser = await res.json()
        }

    }catch(e){
        console.error("Auth init error:", e)
    }

    renderRole()

    await loadBoards()
}

document.addEventListener(
    "DOMContentLoaded",
    initBoards
)