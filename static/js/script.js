const title = document.getElementById("note-title").value
const notes = document.getElementById("note").value

async function saveNote(){

    if(title === "" || notes === ""){
        alert("Please enter title and note")
        return;
    }

    let li = document.getElementById("li").innerHTML = 
    `<h4>Title</h4>
    <p>${title}</p>
    <h4>Note</h4>
    <p class = "notes" > ${notes}</p>
    <button class = "open-but" onclick="toggleNote(this)">Open</button>`;

    document.getElementById("note-list").appendChild(li);

    document.getElementById("note-title").value = "";
    document.getElementById("note").value = "";
}

async function toggleNote(btn) {
    let noteText = btn.parentElement.querySelector(".note");

    if(noteText.style.maxHeight === "none"){

        noteText.style.maxHeight = "50px";
        btn.innerText = "Open" ;
    }

    else{
        noteText.style.maxHeight = "none" ;
        btn.innerText = "Close" ;

    }
}

