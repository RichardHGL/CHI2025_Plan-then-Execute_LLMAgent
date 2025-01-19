async function sendChat() {
    let userInput = document.getElementById("userInput").value.trim();
    if (!userInput) return; // Don't send empty messages

    // Add user's message to the chat area
    appendMessage(userInput, 'user-message');

    // Clear input after sending
    document.getElementById("userInput").value = '';

    try {
        // Start the POST request to send the message
        const response = await fetch('/planning_agent/chain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: userInput })
        });

        let reader = response.body.getReader();
        let decoder = new TextDecoder();

        // Create a container for the bot's message
        let botMessageContainer = createMessageContainer('bot-message');

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            let chunk = decoder.decode(value, { stream: true });
            // Replace newline characters with HTML <br> tags
            chunk = chunk.replace(/\n/g, '<br>');
            botMessageContainer.innerHTML += chunk;
        }
        // Scroll the bot's message container into view
        botMessageContainer.scrollIntoView({ behavior: 'smooth' });
        add_button();
    } catch (error) {
        console.error('Error:', error);
    }
}

async function proceed() {
    try {
        // Start the POST request to send the message
        const response = await fetch('/planning_agent/proceed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: 'proceed' })
        });

        let reader = response.body.getReader();
        let decoder = new TextDecoder();

        // Create a container for the bot's message
        let botMessageContainer = createMessageContainer('bot-message');

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            let chunk = decoder.decode(value, { stream: true });
            // Replace newline characters with HTML <br> tags
            chunk = chunk.replace(/\n/g, '<br>');
            botMessageContainer.innerHTML += chunk;
        }
        // Scroll the bot's message container into view
        botMessageContainer.scrollIntoView({ behavior: 'smooth' });
        // add the buttons after getting the responses
        add_button();
    } catch (error) {
        console.error('Error:', error);
    }
}

function appendMessage(text, className) {
    let messageContainer = createMessageContainer(className);
    messageContainer.innerHTML = text.replace(/\n/g, '<br>'); // Replace newlines with <br>
    document.getElementById('chatArea').appendChild(messageContainer);
    messageContainer.scrollIntoView({ behavior: 'smooth' });
}

function createMessageContainer(className) {
    let div = document.createElement('div');
    div.classList.add('message', className);
    document.getElementById('chatArea').appendChild(div);
    return div;
}

function add_button() {
    document.getElementById('userInput').disabled = true;
    document.getElementById('userInput').setAttribute('placeholder', 'Input disabled, choose one button under the new message');
    document.getElementById('send_button').disabled = true;
    // disable user input and send button before user choose one mode of response
    let addBtn = document.createElement('button');
    addBtn.textContent = 'Proceed';
    // addBtn.className = 'insert-btn';
    addBtn.setAttribute('id', 'addBtn');
    addBtn.addEventListener('click', function(){
        console.log("button Proceed clicked");
        removeElementwithID('addBtn');
        removeElementwithID('reflectionBtn');
        appendMessage('Proceed', 'user-message');
        proceed()
    });

    let reflectionBtn = document.createElement('button');
    reflectionBtn.textContent = 'Reflection';
    reflectionBtn.setAttribute('id', 'reflectionBtn');
    // reflectionBtn.className = 'insert-btn';
    reflectionBtn.addEventListener('click', function(){
        console.log("button Reflection clicked");
        removeElementwithID('addBtn');
        removeElementwithID('reflectionBtn');
        // after one button clicked, users are able to input again
        document.getElementById('userInput').disabled = false;
        document.getElementById('userInput').setAttribute('placeholder', 'Type your message here...');
        document.getElementById('send_button').disabled = false;
        // after users choose reflection, users can send message again to server
    });

    document.getElementById('chatArea').appendChild(addBtn);
    document.getElementById('chatArea').appendChild(reflectionBtn);
}

function removeElementwithID(id) {
    const taskItem = document.getElementById(id);
    taskItem.parentNode.removeChild(taskItem);
}