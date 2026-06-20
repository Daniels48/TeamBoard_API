let draggedCard = null
let pendingChanges = false
const boardId = window.location.pathname.split("/").pop();
const URL_FULL_BOARD = `/api/boards/${boardId}`
let hasUnsavedChanges = false;

async function loadBoard(){

    if(!boardId){return}
    const res = await window.api.get(URL_FULL_BOARD)
    if(!res || !res.ok){return}
    const board = await res.json()
    renderBoards(board)
}

function renderBoards(board) {
    const columns = board.columns;
    const role = board.board_role;
    const time_created_base = board.created_at;
    const public_id = board.public_id;

    function renderColumns(columns, public_id){
        const container = document.getElementById("columns")

        container.innerHTML = ""
        columns.forEach(column => {
            const div = document.createElement("div")
            div.className = "column"

            div.innerHTML = `
                  <div class="container-column">
                      <h3>${column.title} (${column.cards.length}) </h3>
                      <div class="column-menu perm-edit">
                        <button class="menu-btn"onclick="toggleColumnMenu(this)">⋮</button>
                        <div class="column-dropdown">
                            <button class="black perm-edit" onclick="editColumn('${board.public_id}','${column.public_id}')">✏️ Edit</button>
                            <button class="danger perm-manage-members" onclick="deleteColumn('${board.public_id}','${column.public_id}')">🗑️ Delete</button>
                        </div>
                      </div>
                  </div>
                <div class="cards" id="cards-${column.public_id}" data-column-id="${column.public_id}"></div>
                <button class="perm-edit" onclick="createCard('${column.public_id}')">Add Card</button>
            `

            container.appendChild(div)
            const cardsContainer = div.querySelector(".cards")
            cardsContainer.addEventListener("dragover", e => e.preventDefault())

            cardsContainer.addEventListener("drop",
                e => {
                    e.preventDefault()
                    if(!draggedCard){return}
                    const oldContainer = draggedCard.parentElement;
                    const empty = cardsContainer.querySelector(".empty-card");
                    if (empty) {
                        empty.remove();
                    }
                    cardsContainer.appendChild(draggedCard)

                    updateEmptyState(oldContainer);
                    updateEmptyState(cardsContainer);

                    draggedCard = null
                    pendingChanges = true
                    markUnsaved();
                }
            )

            renderCards(cardsContainer, column.cards, column.public_id)
        })
    }
    function renderCards(container,cards,columnId){
        if(cards.length === 0){
            container.innerHTML = '<div class="empty-card">No cards</div>'
            return
        }
        cards.forEach(card => {
            const div =document.createElement("div")
            div.className = "card"
            div.draggable = true
            div.dataset.cardId = card.public_id
            div.addEventListener("dragstart", () => {draggedCard = div})

            div.innerHTML = `
                <div class="card-header">
                    <div class="card-title">${card.title}</div>
                    <div class="card-menu">
                        <button class="menu-btn perm-edit"onclick="toggleCardMenu(this)">⋮</button>
                        <div class="card-dropdown">
                            <button class="edit perm-edit" onclick="editCard('${card.public_id}','${columnId}')">✏️ Edit</button>
                            <button class="danger perm-manage-members" onclick="deleteCard('${card.public_id}','${columnId}')">🗑️ Delete</button>
                        </div>
                    </div>
                </div>

                <div class="card-description">${card.description || ""}</div>
                <div class="card-update">🕒 ${formatUpdated(card.updated_at)}</div>

            `

            container.appendChild(div)
        })
    }
    function renderDataTitle(board){
        document.getElementById("board-title").textContent = board.title
        document.getElementById("board-description").textContent = board.description || ""

        document.getElementById("member-username").addEventListener("input", loadUsers)

        const badge = document.getElementById("board-role-badge")
        badge.textContent = role;
        badge.className = `board-role ${role}`

        const time_board_created = document.querySelector(".icon-data-created");
        time_board_created.innerHTML = formatUpdated(time_created_base, true, board.owner_username);

        const header_col = document.querySelector(".h2-col");
        header_col.textContent = `Columns (${columns.length})`

        const edit_board = document.querySelector(".edit-board");
        const del_board = document.querySelector(".del-board");

        edit_board.onclick = () => editBoard(public_id);
        del_board.onclick = () => deleteBoard(public_id);
    }
    function applyRole(role){
    const class_manage = "perm-manage-members";
    const class_edit = "perm-edit";

    const permissions = {
        admin: {
            edit: true,
            manageMembers: true,
        },
        owner: {
            edit: true,
            manageMembers: true,
        },
        editor: {
            edit: true,
            manageMembers: false,
        },
        viewer: {
            edit: false,
            manageMembers: false,
        }
    }

    const p = permissions[role]
    if(!p.edit){hideClassNameElements(class_edit);}
    if(!p.manageMembers){hideClassNameElements(class_manage);}
}

    renderColumns(columns)
    renderDataTitle(board)
    applyRole(role);
}

function toggleCardMenu(button){
    document.querySelectorAll(".card-dropdown.show")
        .forEach(menu => {
            if(menu !== button.nextElementSibling){
                menu.classList.remove("show")
            }
        })

    button.nextElementSibling.classList.toggle("show")
}

function toggleColumnMenu(button){
    document.querySelectorAll(".column-dropdown.show")
        .forEach(menu => {
            if(menu !== button.nextElementSibling){
                menu.classList.remove("show");
            }
        });

    button.nextElementSibling.classList.toggle("show");
}

function toggleBoardMenu(button) {
    button.nextElementSibling.classList.toggle("show")
}
function toggleCardMenu(button){
    document.querySelectorAll(".card-dropdown.show")
        .forEach(menu => {
            if(menu !== button.nextElementSibling){
                menu.classList.remove("show")
            }
        })

    button.nextElementSibling.classList.toggle("show")
}

//-------------------------------------------------------------
function markUnsaved() {
    document
        .getElementById("unsaved-indicator")
        ?.classList.remove("hidden");

    document
        .getElementById("save-positions-btn")
        ?.classList.remove("hidden");
}

function clearUnsaved() {
    pendingChanges = false;

    document
        .getElementById("unsaved-indicator")
        ?.classList.add("hidden");

    document
        .getElementById("save-positions-btn")
        ?.classList.add("hidden");
}

function updateEmptyState(cardsContainer) {
    const cards = cardsContainer.querySelectorAll(".card");

    if (cards.length === 0) {
        cardsContainer.innerHTML =
            '<div class="empty-card">No cards</div>';
    }
}

async function saveBoard(){
    if(!pendingChanges){return}
    const cards = collectBoardState()
    const url_board_save = `/api/boards/${boardId}/layout`
    const res = await window.api.patch(url_board_save, {cards})
    if(!res || !res.ok){
        alert("Save failed")
        return
    }
    pendingChanges = false
    clearUnsaved();
    await loadBoard();
}

function collectBoardState(){
    const cards = []
    document.querySelectorAll(".cards").forEach(column => {
            const columnId = column.dataset.columnId
            column.querySelectorAll(".card").forEach((card, index) => {
                    cards.push({card_id: card.dataset.cardId,column_id:columnId,position:index})
                })
        })
    return cards
}
//-------------------------------------------------------------

async function createColumn(){
    const title = prompt("Column title")
    if(!title){return}
    const url_column = `/api/boards/${boardId}/columns`
    const res = await window.api.post(url_column, {title})

    if(!res || !res.ok){alert("Failed to create column");return}
    await loadBoard();
}

async function createCard(columnId){
    const title = prompt("Card title")
    if(!title){return}
    const description = prompt("Description (optional)") || ""

    const url_card = `/api/columns/${columnId}/cards`
    const res = await window.api.post(url_card, {title,description})

    if(!res || !res.ok){
        alert("Failed to create card")
        return
    }
    await loadBoard()
}

async function editCard(cardId, columnId){
    const title = prompt("New title")
    if(title === null){return}
    const description = prompt("New description")
    const url_card_edit = `/api/cards/${cardId}`
    const res = await window.api.patch(url_card_edit, {title,description})

    if(!res || !res.ok){
        alert("Update failed")
        return
    }
    await loadBoard()
}

async function deleteCard(cardId,columnId){
    const confirmed = confirm("Delete card?")
    if(!confirmed){return}
    const url_del = `/api/cards/${cardId}`;
    const res = await window.api.del(url_del);
    if(!res || !res.ok){
        alert("Delete failed")
        return
    }
    await loadBoard()
}

async function editColumn(boardId, columnId){
    const title = prompt("New column title");
    if (title === null || !title.trim()) {return;}
    const res = await window.api.patch(`/api/boards/${boardId}/columns/${columnId}`,{title: title.trim()});
    if (!res?.ok) {
        alert("Update failed");
        return;
    }
    await loadBoard();
}

async function deleteColumn(boardId, columnId){
    const confirmed = confirm("Delete column and all cards inside?");
    if (!confirmed) { return;}
    const res = await window.api.del(`/api/boards/${boardId}/columns/${columnId}`);
    if (!res?.ok) {
        alert("Delete failed");
        return;
    }
    await loadBoard();
}

async function editBoard(boardId){
    const title = prompt("New board title");
    const description = prompt("New description board");

    if (title === null || !title.trim() || description===null) {return;}
    const res = await window.api.patch(`/api/boards/${boardId}`,{title: title.trim(), description: description.trim()});
    if (!res?.ok) {
        alert("Update failed");
        return;
    }
    await loadBoard();
}

async function deleteBoard(boardId){
    const confirmed = confirm("Delete board and all cards and column inside?");
    if (!confirmed) { return;}
    const res = await window.api.del(`/api/boards/${boardId}`);
    if (!res?.ok) {
        alert("Delete failed");
        return;
    }
    window.location.href = '/boards'
}

//-------------------------------------------------------------


//-------------------------------------------------------------
async function addMember(){
    const username =document.getElementById("member-username").value.trim()
    const role =document.getElementById("member-role").value

    if(!username){
        alert("Enter username")
        return
    }

    const res = await window.api.post(`/api/members/${boardId}`,{username,role})

    const data = await res.json();

    if(!res || !res.ok){
        alert(`ERROR - ${data.error}`)
        return
    }

    document.getElementById("member-username").value = ""
    await loadMembers()
}

async function loadUsers(){
    const q = document.getElementById("member-username").value.trim()
    if(q.length < 2){return}

    const res = await window.api.get(`/api/users/search?q=${encodeURIComponent(q)}`)

    if(!res || !res.ok){return}

    const users = await res.json()

    const datalist = document.getElementById("users-list")
    datalist.innerHTML = ""

    users.forEach(user => {
        const option = document.createElement("option")
        option.value = user.username
        datalist.appendChild(option)
    })
}

async function loadMembers(){
    const res = await window.api.get(`/api/members/${boardId}`)
    if(!res || !res.ok){
        alert("Failed to load members")
        return
    }
    const data = await res.json()
    renderMembers(data)
}

async function removeMember(userId){
    const confirmed = confirm("Remove member?")
    if(!confirmed){return}
    const res = await window.api.del(`/api/members/${boardId}/${userId}`)
    const data = await res.json();

    if(!res || !res.ok){
        alert(`ERROR - ${data.error}`)
        return
    }
    await loadMembers()
}

async function changeRole(username, currentRole){
    const role = currentRole === "editor"? "viewer" : "editor"
    const res = await window.api.patch(`/api/members/${boardId}/${username}`,{ role })
    const data = await res.json();
    if(!res || !res.ok){
        alert(`ERROR - ${data.error}`)
        return
    }

    await loadMembers()
}

function renderMembers(data){
    const editorsContainer = document.getElementById("editors-list")
    const viewersContainer = document.getElementById("viewers-list")

    editorsContainer.innerHTML = ""
    viewersContainer.innerHTML = ""

    document.getElementById("owner-name").textContent = data.owner.username

    data.members.forEach(member => {
        const div = document.createElement("div")
        div.className = "member-item"
        div.innerHTML = `
            <span>${member.username}</span>
            <div class="member-actions">
                <button class="icon-btn" onclick="changeRole('${member.username}','${member.role}')">🔄</button>
                <button class="icon-btn delete" onclick="removeMember('${member.username}')">❌</button>
            </div>
        `
        if(member.role === "editor"){
            editorsContainer.appendChild(div)
        }else{
            viewersContainer.appendChild(div)
        }
    })
}
//-------------------------------------------------------------

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

function openMembersDialog(){loadMembers();document.getElementById("members-dialog").showModal()}
function closeMembersDialog(){document.getElementById("members-dialog").close()}
function isAdmin(role){return role === "admin"}
function isOwner(role){return role === "owner"}
function isEditor(role){return role === "editor"}
function isViewer(role){ return role === "viewer"}
function canManageMembers(role){return isAdmin(role) || isOwner(role)}
function canEditBoard(role){return isAdmin(role) || isOwner(role) || isEditor(role)}
function hideClassNameElements(className){
    document
        .querySelectorAll(`.${className}`)
        .forEach(element => {element.style.display = "none"})
}

document.addEventListener("click", e => {
    if(!e.target.closest(".card-menu")){
        document
            .querySelectorAll(".card-dropdown.show")
            .forEach(menu => menu.classList.remove("show"))
    }

    if (!e.target.closest(".column-menu")) {
        document.querySelectorAll(".column-dropdown.show")
            .forEach(menu => menu.classList.remove("show"));
    }

    if (!e.target.closest(".three-dot")) {
        document.querySelectorAll(".board-dropdown.show")
            .forEach(menu => menu.classList.remove("show"));
    }


})

document.addEventListener("DOMContentLoaded",loadBoard)