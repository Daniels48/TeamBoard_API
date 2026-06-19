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

function formatUpdated(dateString, isCreated = false, by = null) {
    const date = new Date(dateString);
    const now = new Date();

    let text = isCreated ? "Created" : "Updated";

    if (by) {
        text += ` by <span class="owner-name">${by}</span>`;
    }

    const diffMs = now - date;
    const diffMinutes = Math.floor(diffMs / 1000 / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMinutes < 1) return `${text} just now`;
    if (diffMinutes < 60) return `${text} ${diffMinutes}m ago`;
    if (diffHours < 24) return `${text} ${diffHours}h ago`;
    if (diffDays === 1) return `${text} yesterday`;
    if (diffDays < 30) return `${text} ${diffDays} days ago`;

    return `${text} ${date.toLocaleDateString()}`;
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
            <div class="board-header-data">
                <h3>${board.title}</h3>
                <div class="board-role ${board.role.toLowerCase()}">${board.role}</div>
            </div>
            <div class="board-description">${board.description || "No description"}</div>
            <div class="board-footer">
                <div class="board-count-data">
                    <div class="board-columns-count">${board.columns_count} columns</div>
                    <div clas="board-dot-count">•</div>
                    <div clas="board-cards-count">${board.cards_count} cards</div>
                </div>
                <span class="created-board">${formatUpdated(board.created_at, true, board.owner_username)}</span>
            </div>
        `
        div.onclick = () => {window.location.href =`/boards/${board.public_id}`}

        container.appendChild(div)
    })
}


async function createBoard(){
    const title = prompt("Card title").trim()
    const description = prompt("Description (optional)").trim() || ""
    if(!title){
        alert("Введите название")
        return
    }
    const url_boards = "/api/boards"
    const res = await window.api.post(url_boards,  {title, description});

    if(!res || !res.ok){
        alert("Ошибка создания доски")
        return
    }
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