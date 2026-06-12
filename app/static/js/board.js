let boardId = null
let draggedCard = null
let pendingChanges = false
const params = new URLSearchParams(window.location.search)
boardId = params.get("id")
const URL_FULL_BOARD = `/api/boards/${boardId}/full`


async function loadBoard(){
    if(!boardId){return}
    const res = await window.api.get(URL_FULL_BOARD)
    if(!res || !res.ok){return}
    const board = await res.json()
    document.getElementById("board-title").textContent = board.title
    document.getElementById("board-description").textContent =board.description || ""
    renderColumns(board.columns)
}


function renderColumns(columns){
    const container = document.getElementById("columns")
    container.innerHTML = ""
    columns.forEach(column => {
        const div = document.createElement("div")
        div.className = "column"

        div.innerHTML = `
            <h3>${column.title}</h3>
            <div class="cards" id="cards-${column.public_id}" data-column-id="${column.public_id}"></div>
            <button onclick="createCard('${column.public_id}')">Add Card</button>
        `

        container.appendChild(div)
        const cardsContainer = div.querySelector(".cards")
        cardsContainer.addEventListener("dragover", e => e.preventDefault())

        cardsContainer.addEventListener("drop",
            e => {
                e.preventDefault()
                if(!draggedCard){return}
                cardsContainer.appendChild(draggedCard)
                draggedCard = null
                pendingChanges = true
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
            <div class="card-title">${card.title}</div>
            <div class="card-description">${card.description || ""}</div>
            <div class="card-actions">
                <button onclick="editCard('${card.public_id}','${columnId}')">Edit</button>
                <button class="delete" onclick="deleteCard('${card.public_id}','${columnId}')">Delete</button>
            </div>
        `
        container.appendChild(div)
    })
}


////////////////////////////////////////
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
    await loadColumns()
    alert("Saved")
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
/////////////////////////////////////////

async function createColumn(){
    const input = document.getElementById("column-title")
    const title = input.value.trim()
    if(!title){return}
    const url_column = `/api/boards/${boardId}/columns`
    const res = await window.api.post(url_column, {title})

    if(!res || !res.ok){return}
    input.value = ""
    await loadColumns()
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
    await loadCards(columnId)
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
    await loadCards(columnId)
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
    await loadCards(columnId)
}


document.addEventListener("DOMContentLoaded",loadBoard)