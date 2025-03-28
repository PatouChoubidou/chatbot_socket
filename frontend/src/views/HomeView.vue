<script setup>

import { ref, onMounted, onUpdated } from 'vue'
import mic from "../assets/mic.svg";
import MyToggle from "../components/MyToggle.vue"

var socket = null;
// const incomingMessage = ref("")
const message = ref("")
const messages = ref([])
const upload_files = ref([])
const docs = ref([])

const isRecording = ref(false)
const autoPlayLLMAnswer = ref(false)
const isFullTextSearch = ref(true)
var recorder = null;
var recStream = null;
var audioChunks = [];

const isDragging = ref(false)

// pdf, txt, rtf, docx, odt
const allowedUploadFileMimeTypes = [
  "application/pdf",
  "text/plain",
  "text/rtf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.oasis.opendocument.text"
]


// vue - on page load do
onMounted(() => {
    startSocket();
    getListOfDocs()
})


// vue - on value update do
onUpdated(()=> { 
    const lastAnswer = document.querySelector("div.assistant:last-of-type");
    const lastQuestion = document.querySelector("div.user:last-of-type");
    const container = document.getElementById("msg_wrapper");
    
    if (lastAnswer){
        
        const finalY = container.scrollHeight - (lastAnswer.offsetHeight + 100 )
        container.scrollTo({top: finalY, left: 0, behavior: "smooth"});
    }
    container.scrollTo({top: container.scrollHeight, left: 0, behavior: "smooth"});
})


const clearFiles = (e) => {
    /* 
    Clears the frontend representation of the dropped files
    */
    upload_files.value = [];
    getListOfDocs()
}

const toggleFullTextSearch = () =>{

    let status = "ON"
    if (!isFullTextSearch.value){
        status = "OFF"
    }
    if (isFullTextSearch.value){
        status = "ON"
    }
    
    const transporterObj = {
            "type": "string",
            "name": "",
            "mime-type": "",
            "data": "@isFullTextSearchToggle-"+status,
          }

    socket.send(JSON.stringify(transporterObj))
    console.log("full text search toggled", status)
}


const dragover = (e) => {
    e.preventDefault();
    isDragging.value = true;
}


const dragleave = (e) => {
    isDragging.value = false;
}

const uploadFileViaSocket = async(file) =>{
    /* 
    Takes a file, encodes it as base64 string and send it to the server in my transporter obj
    */
    console.log("file before encoding: ",file)
    blob2base64(file, file.type).then((f)=>{
        const fileName = file.name || ""
        const mimeType = file.type || ""
       
        const transporterObj = {
          "type": "binary",
          "name": fileName,
          "mime-type": mimeType,
          "data": f,
        }
        console.log("file data after encoding", f);
        socket.send(JSON.stringify(transporterObj))
        getListOfDocs()
    })   
}


const drop = async(e) => {
    /* 
    This func takes some files which have been dragged 
    but send only the fist selected to the server for processing
    */
    
    // clear all files
    clearFiles()
    e.preventDefault();
     
    if (e.dataTransfer.items) {
        const newFiles = e.dataTransfer.files;
        // console.log("new files", newFiles);
        
        // Use DataTransferItemList interface to access the file(s)
        [...e.dataTransfer.items].forEach((item, i) => {
            // If dropped items aren't files, reject them
            if (item.kind === "file") {
                const file = item.getAsFile();
                console.log(`… file[${i}].name = ${file.name}`);
                upload_files.value.push(file);
            }
        });
    } else {
        // else use DataTransfer interface to access the file(s)
        [...e.dataTransfer.files].forEach((file, i) => {
            console.log(`… file[${i}].name = ${file.name}`);
            upload_files.value.push(file);
        });
    }
    /* send only first pdf to server */
    console.log("files to be uploaded", upload_files);
    console.log("mimeType of thing to be uploaded", upload_files.value[0].type);

    if( allowedUploadFileMimeTypes.includes(upload_files.value[0].type) ) {
        uploadFileViaSocket(upload_files.value[0])
        systemMessage(`Uploading file: "${upload_files.value[0].name}"`);
    } else {
        systemMessage(`Ahhh my poor belly. I currently digest pdf, txt, odt, docx or rtf file format.\n You fed me "${upload_files.value[0].name}"`);
        console.log(`Drop file format is no pdf, txt, odt, docx or rtf.`);
        clearFiles();
    } 
} 


const systemMessage = (txt) => {
    const options = {
      year: "numeric",
      month: "numeric",
      day: "numeric",
      hour: "numeric",
      minute: "numeric",
      second: "numeric"
    };
    
    let now = Date.now();
    let date = new Date(now).toLocaleString("de-De", options)

    messages.value.push({
        "role": "system",
        "content": txt,
        "created_at": date
    })
}


const downloadAndAddAudio = async() => {
    /* 
    Downloads the latest tts created audio as .wav from the server and 
    appends it to the last answer
    uncomment the last lines to play the audio right away
    */

    const prevAudio = document.querySelector("div.assistant:last-of-type audio");
    if (prevAudio){
      prevAudio.remove()
    }
    const response = await fetch("http://0.0.0.0:8000/wav");
    const data = await response.arrayBuffer();
    if(data.byteLength != 0){
        const blob = new Blob([data], { type: "audio/wav" });
        const blobUrl = URL.createObjectURL(blob);
        const audio = new Audio();
        audio.src = blobUrl;
        audio.controls = true;
        const lastAnswer = document.querySelector("div.assistant:last-of-type div");
        if(lastAnswer){
            lastAnswer.appendChild(audio);
        }
        // for autoplay the anwswer switch bool
        if(autoPlayLLMAnswer.value){ 
            audio.play(); 
        }
       
    } 
}


const recordAudio = async() => {
    /* 
    Creates a recorder and starts recording
    */
    try{
        console.log("start recording")
        isRecording.value = true;
        recStream = await navigator.mediaDevices.getUserMedia({audio: true});
        const options = {
            mimeType: "audio/webm",
        };
        recorder = new MediaRecorder(recStream, options); // records as webm needs to be converted
        audioChunks = []
        recorder.ondataavailable = (e) => { audioChunks.push(e.data); }
        recorder.start();
    } catch (err) {
        console.log("a problem while recording audio has occured", err)
    }
}


const stopRecordAudio = async() => {
    /* 
    Stops the recording and sends the recording to the server
    Resets the recorder afterwards
    */

    systemMessage("sending audio...");

    console.log("stop recording")
    isRecording.value = false;
    let mimeType = recorder.mimeType;
    recorder.stop();
    isRecording.value = false;
    // when the recorder stops do
    recorder.addEventListener("stop", (e) => {
        //create a single blob object, as one might have gathered a few Blob objects that need to be joined 
        const audioBlob = new Blob(audioChunks, { type: mimeType });
        
        // blob to string and send to server
        blob2base64(audioBlob).then((base64)=>{
            
            const transporterObj = {
                "type": "binary",
                "name": "audioQuestion",
                "mime-type": mimeType,
                "data": base64,
            }
            socket.send(JSON.stringify(transporterObj))
        })
    });

    // stop the recorder and cancel streams
    recorder.stream.getTracks()
        .forEach(track => track.stop())
    // reset stream and recorder
    recStream = null;
    recorder = null;      
}


const blob2base64 = (blob, mimeType) => {
    /* 
    Promiss that converts a blob into base64 encoded string
    */
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const dataUrlPrefix = `data:${mimeType};base64,`;
        const base64WithDataUrlPrefix = reader.result;
        // console.log("base 64 before stripping type data: ", base64WithDataUrlPrefix)
        const base64 = base64WithDataUrlPrefix.replace(dataUrlPrefix, '');
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
};


const getListOfDocs = async() => {
    /* 
    Download a list of files which are stored on the server
    */
    try{
      const response = await fetch("http://0.0.0.0:8000/doc-list");
      const data = await response.json()
      console.log("files on the server:", data) 
      docs.value = data
    } catch{
      console.log("error fetching list of files")
    }

}


const startSocket = (e) => {
    /* 
    Start the socket and create event listeners
    */
    socket = new WebSocket("http://localhost:8000/chat")
    
    // Connection opened
    socket.addEventListener("open", (e) => {
        console.log("Websocket connection opened");
    });

    // receive messages
    socket.addEventListener("message", (e) => {
        console.log("message from server:", e);
        const serverResponse = e.data;
        const transporterObj = JSON.parse(serverResponse)

        if (transporterObj['type'] == 'string') {
            // const responseAsJsonLine = responseAsJson.replace("\\n", "\n")
            console.log("incoming parsed json: ", transporterObj, "type:", typeof(transporterObj))

            const messageList = JSON.parse(transporterObj['data'])
            messages.value = messageList
          
            downloadAndAddAudio()
   
        }
        // if type is buffer do
        if (transporterObj['type'] == 'binary') {
            console.log('incoming binary:', transporterObj)
        }
    })

    // listen for closing
    socket.addEventListener("close", (e) => {
        console.log("socket is closing", e);  
    })
}


const stopSocket = () => {
    socket.close()
}


const newChat = () => {
    /* 
    Reset the chat history on the server
    */
    if(socket){
        const msg = "@resetChatHistory"
        const transporterObj = {
          "type": "string",
          "name": "function call - reset chat history",
          "mime-type": "",
          "data": msg,
        }
      socket.send(JSON.stringify(transporterObj))
    }
}


const clearDocs = () => {
    /* 
    Delete all documents that were uploaded to the server
    */
    if(socket){
        const msg = "@clearDocuments"
        const transporterObj = {
          "type": "string",
          "name": "function call - clear docs",
          "mime-type": "",
          "data": msg,
        }
      socket.send(JSON.stringify(transporterObj))
      getListOfDocs()
    }
    console.log("clearing docs");
}


const sendWsMessage = () => {
    /* 
    Sends the user input to the server
    */
    if(socket){
      const msg = message.value
      console.log("msg: ", msg)

      const transporterObj = {
          "type": "string",
          "name": "question",
          "mime-type": "",
          "data": msg,
        }
      socket.send(JSON.stringify(transporterObj))

      // this is the waiting message
      systemMessage("Generating response...")
    }
    else {
      startSocket()
    } 
    // reset input 
    message.value = ""
}

</script>

<template>
  <main>
    <MyToggle v-model="autoPlayLLMAnswer" label="play audio anwser"></MyToggle>
    <MyToggle v-model="isFullTextSearch" label="use full text" @click="toggleFullTextSearch"></MyToggle>
    <div :id="'chat_container'">
      <div class="dropzone-container"
        @dragover="dragover"
        @dragleave="dragleave"
        @drop="drop"
        accept=".pdf">
        <!--
        <input type="file" multiple name="file" id="fileInput" class="hidden-input" @change="onChange" ref="file" accept=".pdf,.jpg,.jpeg,.png" />
        -->
        <div :id="'msg_wrapper'">
            <div v-for="msg in messages" :class="msg.role">
              <p>{{ msg.content.replace("\n", "\n") }}</p>
              <span>{{ msg.created_at }}</span>
              <div></div>
            </div>
          </div>
        <div :id="'writer'">
            <input @keyup.enter="sendWsMessage" v-model="message" placeholder="ask something" name="send_message" />
            <button @click="sendWsMessage" >&#8679;</button>
            <button :class="isRecording && 'recording'" @mousedown="recordAudio" @mouseup="stopRecordAudio">
              <img v-if="isRecording" src="../assets/mic.svg">
              <img v-if="!isRecording" src="../assets/mic2.svg">
            </button>
        </div>
      </div>
    </div>
    <div v-if="docs" :id="'file__list__wrapper'">
      <div v-for="doc_name in docs" :class="'file__list__item'"> 
              <span>PDF: {{ doc_name }}</span>    
      </div>
    </div>
    <div>
      <button @click="newChat">new Chat</button>
      <button @click="clearDocs">clear docs</button>
    </div>
  </main>
</template>


<style scoped>
h1{
  text-align: center;
}

button{
  padding: 10px 20px;
  border-radius: 0px 0px 20px 20px;
  background-color: aquamarine;
  border: 0px;
}

#chat_container{
  border:solid 2px aquamarine;
  padding: 20px;
  max-width: 500px;
  border-radius: 15px;
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

#msg_wrapper{
  width: 400px;
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  background-color: white;
  border-radius: 4px;
  height: 400px;
  overflow-y: auto;
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;  
}


#msg_wrapper > :first-child {
    margin-top: auto !important;
    /* use !important to prevent breakage from child margin settings */
}

#msg_wrapper > div{
  position: relative;
  display: block;
  padding: 10px;
  border-radius: 20px;
  margin: 15px 0;
}

#msg_wrapper > div span{
  display: block;
  color: rgb(13, 105, 74);
  background-color: rgb(233, 233, 233);
  font-size: 8px;
  padding: 2px 10px 2px 10px;
  border-radius: 10px 10px 0px 0px;
  position: absolute;
  top: -17px;
  left: 16px;
  width: auto;
}

#msg_wrapper div.user {
  max-width: 90%;
  min-width: 40%;
  padding: 10px 20px;
  align-self: flex-end;
  background-color: rgb(22, 195, 137);
  color:aliceblue;
}

#msg_wrapper div.system {
  align-self: flex-start;
  max-width: 90%;
  padding: 10px 20px;
  background-color: rgb(0, 200, 250); 
}

#msg_wrapper div.assistant {
  white-space: pre-wrap; /* this keeps line breaks*/ 
  align-self: flex-start;
  max-width: 90%;
  padding: 10px 20px;
  background-color: rgb(220, 220, 220); 
}

#msg_wrapper > div.assistant > div {
  margin: 20px 0  10px 0;
}

#msg_wrapper div.assistant audio {
  display: block;
  margin: 10px 0;
}

#writer{
  margin-top: 10px;
}

#writer input{
  padding: 15px 20px;
  width: 70%;
  border: solid 2px aquamarine;
  border-top-left-radius: 20px;
  border-top-right-radius: 0px;
  border-bottom-left-radius: 20px;
  border-bottom-right-radius:0px;
  background-color: rgb(220, 220, 220); 
}

#writer input:focus{
    outline-color: rgb(0, 237, 158);
}

#writer button:nth-last-child(2){
  font-weight: 800;
  font-size: 30px;
  color:rgb(0, 130, 86);
  vertical-align: middle;
  padding: 9px 5px 5px 5px;
  width: 15%;
  background-color: aquamarine;
  border: 0;
  border-top-left-radius: 0px;
  border-top-right-radius: 0px;
  border-bottom-left-radius: 0px;
  border-bottom-right-radius: 0px;
}

#writer > button:hover, 
#writer button:nth-last-child(1).recording:hover{
    background-color: rgb(0, 200, 250);
}

#writer button:nth-last-child(1){
  font-weight: 800;
  font-size: 30px;
  color:rgb(0, 130, 86);
  vertical-align: middle;
  padding: 13px 3px 2px 3px;
  width: 15%;
  background-color: aquamarine;
  border: 0;
  border-top-left-radius: 0px;
  border-top-right-radius: 20px;
  border-bottom-left-radius: 0px;
  border-bottom-right-radius: 20px;
}

#writer button:nth-last-child(1) img{
  width: 28px;
  height: auto;
  filter: invert(50%) sepia(85%) saturate(2500%) hue-rotate(90deg) brightness(70%) contrast(100%);
}

#writer button:nth-last-child(1).recording{
    background:rgb(7, 248, 248);
}

#file__list__wrapper{
  display: flex;
  flex-direction: column;
  border:solid 2px aquamarine;
  border-top: 0;
  max-width: 500px;
  border-radius: 15px;
  border-top-left-radius: 0px;
  border-top-right-radius: 0px;
  border-bottom-left-radius: 0px;
  border-bottom-right-radius: 10px;
}

.file__list__item{
  font-size: 0.8rem;
  padding: 5px 20px;
}


</style>
