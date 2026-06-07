let boardId = null
let draggedCard = null
let pendingChanges = false


async function loadBoard(){
    const params =new URLSearchParams(window.location.search)
    boardId = params.get("id")
    if(!boardId){return}
    const res = await apiFetch(`/api/boards/${boardId}`)
    if(!res || !res.ok){return}
    const board = await res.json()
    document.getElementById("board-title").textContent = board.title
    document.getElementById("board-description").textContent = board.description || ""
    await loadColumns()
}

async function loadColumns(){
    const res = await apiFetch(`/api/boards/${boardId}/columns`)
    if(!res || !res.ok){return}
    const columns = await res.json()
    const container = document.getElementById("columns")
    container.innerHTML = ""
    columns.forEach(async column => {
        const div = document.createElement("div")
        div.className = "column"
        div.innerHTML = `
            <h3>${column.title}</h3>
            <div class="cards" id="cards-${column.public_id}" data-column-id="${column.public_id}"></div>
            <button onclick="createCard('${column.public_id}')">Add Card</button>
        `

        container.appendChild(div)
        const cardsContainer = div.querySelector(".cards")
        cardsContainer.addEventListener("dragover",e => {e.preventDefault()})


        cardsContainer.addEventListener("drop",e => {
            e.preventDefault()
            if(!draggedCard){return}
            cardsContainer.appendChild(draggedCard)
            draggedCard = null
            pendingChanges = true
        })

        await loadCards(column.public_id)
    })
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

async function saveBoard(){
    if(!pendingChanges){return}
    const cards = collectBoardState()
    const res = await apiFetch(`/api/boards/${boardId}/layout`,
            {
                method:"PATCH",
                headers:{
                    "Content-Type":
                    "application/json"
                },
                body:JSON.stringify({
                    cards
                })
            }
        )
    if(!res || !res.ok){
        alert("Save failed")
        return
    }
    pendingChanges = false
    await loadColumns()
    alert("Saved")
}

async function loadCards(columnId){
    const res = await apiFetch(`/api/columns/${columnId}/cards`)
    if(!res || !res.ok){return}
    const cards = await res.json()
    const container = document.getElementById(`cards-${columnId}`)
    container.innerHTML = ""
    if(cards.length === 0){
        container.innerHTML = `
            <div class="empty-card">
                No cards
            </div>
        `
        return
    }

    cards.forEach(card => {
        const div = document.createElement("div")
        div.className = "card"
        div.draggable = true
        div.dataset.cardId = card.public_id
        div.addEventListener("dragstart",() => {draggedCard = div})

         div.innerHTML = `
            <div class="card-title">${card.title}</div>
            <div class="card-description">${card.description || ""}</div>
            <div class="card-actions">
                <button onclick="editCard('${card.public_id}', '${columnId}')">Edit</button>
                <button onclick="deleteCard('${card.public_id}', '${columnId}')">Delete</button>
            </div>`
        container.appendChild(div)
    })
}

async function createColumn(){
    const input = document.getElementById("column-title")
    const title = input.value.trim()
    if(!title){return}
    const res = await apiFetch(
            `/api/boards/${boardId}/columns`,
            {
                method:"POST",
                headers:{
                    "Content-Type":
                    "application/json"
                },
                body:JSON.stringify({
                    title
                })
            }
        )

    if(!res || !res.ok){return}
    input.value = ""
    await loadColumns()
}

async function createCard(columnId){
    const title = prompt("Card title")
    if(!title){return}
    const description = prompt("Description (optional)") || ""
    const res = await apiFetch(`/api/columns/${columnId}/cards`,
            {
                method:"POST",
                headers:{
                    "Content-Type":
                    "application/json"
                },
                body:JSON.stringify({
                    title,
                    description
                })
            }
        )

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
    const res = await apiFetch(`/api/cards/${cardId}`,
            {
                method:"PATCH",
                headers:{
                    "Content-Type":
                    "application/json"
                },
                body:JSON.stringify({
                    title,
                    description
                })
            }
        )

    if(!res || !res.ok){
        alert("Update failed")
        return
    }
    await loadCards(columnId)
}

async function deleteCard(cardId,columnId){
    const confirmed = confirm("Delete card?")
    if(!confirmed){return}
    const res = await apiFetch(`/api/cards/${cardId}`,{method:"DELETE"})
    if(!res || !res.ok){
        alert("Delete failed")
        return
    }
    await loadCards(columnId)
}


document.addEventListener(
    "DOMContentLoaded",
    loadBoard
)