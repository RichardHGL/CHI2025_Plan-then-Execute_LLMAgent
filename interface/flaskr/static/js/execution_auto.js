var action_list = [];
var predicted_action = "unknown";
var default_input = {};
var task_done = false;
var after_execution = false;
var attention_check_flag = false;
var message_list = [];
// global variable as placeholder

async function taskStart() {
    document.getElementById('userInput').disabled = true;
    document.getElementById('userInput').setAttribute('placeholder', 'Input disabled, waiting for the AI response');
    document.getElementById('send_button').disabled = true;
    append_jumping_dots();
    // In the beginning of the task, prepare agent and obtain potential actions and schema
    try {
        // Start the POST request to send the message
        const response = await fetch('/planning_agent/potential_actions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 'message': 'task starts' })
        }).then(response => response.json()).then(data => {
            action_list = data["actions"];
            // We can list all potential actions here
            // console.log(action_list);
            // removeElementwithID('jumping_dots');
            appendMessage('AI system is prepared, let us start', 'bot-message');
        });
    } catch (error) {
        console.error('Error:', error);
    } finally{
        removeElementwithID('jumping_dots');
    }
}

async function taskEnd() {
    appendMessage('AI system has followed the plan and instruction to execute the task, you can click the button to move forward', 'bot-message');
    // show the button to next task
    document.getElementById('submit_button').style.display = "block";
    // block all inputs and buttons

    document.getElementById('userInput').disabled = true;
    document.getElementById('userInput').setAttribute('placeholder', 'Taks done, please move to the next task');
    document.getElementById('send_button').disabled = true;
    document.getElementById('send_button').style.disaplay = "none";
    //save all the messages into the action task_end
    record_user_action(action="task_end", action_input={"message_list": message_list})
}

async function sendChat() {
    let button_name = document.getElementById("send_button").innerHTML;
    if (button_name === "Send"){
        // this means reflection from user input to a specific step
        // re-execute this step with user feedback
        let userInput = document.getElementById("userInput").value.trim();
        if (!userInput) return; // Don't send empty messages

        // Add user's message to the chat area
        appendMessage(userInput, 'user-message');

        // Clear input after sending
        document.getElementById("userInput").value = '';

        await append_cur_step(start_status = false);
        // one_step(userInput=userInput);
        // To-do: check whether we need to define a new way to conduct reflection
        if (after_execution){
            // after execution, user send reflection message will trigger step back mode
            action_prediction(userInput=userInput, mode='step_back');
        } else {
            // before execution, user send reflection message will trigger reflection mode
            action_prediction(userInput=userInput, mode='reflection');
        }
    }
    else{
        await taskStart();
        // starting with one step of the plan
        // append the cur step to message area
        await append_cur_step(start_status=true);
        // show the exectuion result
        // one_step(userInput = "None");
        action_prediction(userInput="None", mode='prediction');
    }
}

async function append_cur_step(start_status = false){
    // first show users the current step
    let userInput = "None";
    // Start the POST request to send the message
    const x_ = await fetch('/planning_agent/cur_step', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: userInput })
    })
    .then(response => response.json()).then(data => {
        // Handle the JSON data
        let tp_query = data["query"];
        let cur_step = data["step"];
        // console.log(data);
        if (start_status){
            // only show the task in the beginning
            appendMessage("The task is: \n" + tp_query, 'user-message');
        }
        // cur_step = cur_step.replace(/[/\n]+/g, '<br>\r');
        // console.log(cur_step)
        appendMessage('Please execute the current step:\n' + cur_step, 'user-message');
        document.getElementById("send_button").innerHTML = "Send";
        // document.getElementById('userInput').setAttribute('placeholder', 'Type your message here...');
    })
    .catch(error => console.error(error));
}

async function action_execution(tool_name, tool_input) {
    document.getElementById('userInput').setAttribute('placeholder', 'Waiting for the AI response');
    append_jumping_dots();
    // Then show agent execution output
    try {
        // Start the POST request to send the message
        const response = await fetch('/planning_agent/action_execution', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 'tool_name': tool_name, 'tool_input': tool_input })
        }).then(response => response.json()).then(data => {
            // removeElementwithID('jumping_dots');
            appendMessage(data['message'], 'bot-message');
            // now we only conduct attention check after the execution of the first step
            attention_check_flag = data['attention_check'];
            task_done = data['task_end'];
            // console.log(task_done);
            document.getElementById('userInput').setAttribute('placeholder', 'Input disabled, choose one button under the new message');
            if (task_done){
                taskEnd();
            }
        });
    } catch (error) {
        console.error('Error:', error);
    } finally {
        removeElementwithID('jumping_dots');
        record_user_action(action="execute_action", action_input={ 'tool_name': tool_name, 'tool_input': tool_input })
        // if
        if (!task_done){
            add_button_after_execution();
        }
        after_execution = true;
    }
}

function append_jumping_dots(){
    // let div = document.createElement('div');
    // div.setAttribute('id', 'jumping_dots');

    let span_0 = document.createElement('span');
    span_0.setAttribute('class', 'jumping-dots');
    span_0.setAttribute('id', 'jumping_dots');

    let span_1 = document.createElement('span');
    span_1.setAttribute('class', 'dot-1');

    let span_2 = document.createElement('span');
    span_2.setAttribute('class', 'dot-2');

    let span_3 = document.createElement('span');
    span_3.setAttribute('class', 'dot-3');

    span_0.appendChild(span_1);
    span_0.appendChild(span_2);
    span_0.appendChild(span_3);
    // div.appendChild(span_0);
    document.getElementById("dots").appendChild(span_0);
    // let messages = document.getElementsByClassName("message");
    // console.log(messages)
    // const last_message = messages[messages.length - 1];
    // last_message.parentNode.insertBefore(span_0, last_message.nextSibling);
}

async function record_user_action(action = "proceed", action_input = {}) {
    url = '/planning_agent/action_recording';
    try {
        // Start the POST request to send the message
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            // here the message does not matter
            body: JSON.stringify({ 'action': action, 'action_input': action_input})
        })
    } catch (error) {
        console.error('Error:', error);
    }
}

async function attention_check(userInput="None", mode="prediction") {
    append_jumping_dots();
    url = '/planning_agent/action_prediction';
    let message = "None";
    try {
        // Start the POST request to send the message
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            // here the message does not matter
            body: JSON.stringify({ 'message': userInput, 'mode': mode})
        }).then(response => response.json()).then(data => {
            // Handle the JSON data
            // Here, we get attention check message from data wiht data['log'] + extra text
            predicted_action = data['tool_name'];
            default_input = data['tool_input'];
            // console.log(predicted_action);
            // console.log(default_input);
            // remove the jumping dots before we append message
            // removeElementwithID('jumping_dots');
            appendMessage(data['log'] + "This is one attention check, please click Feedback", 'bot-message');
        });
        // .catch(error => console.error(error));
    } catch (error) {
        console.error('Error:', error);
    } finally {
        removeElementwithID('jumping_dots');
        add_button_attention_check();
    }
}

async function action_prediction(userInput="None", mode="prediction") {
    // when waiting for the response, show the jumping dots
    append_jumping_dots();
    url = '/planning_agent/action_prediction';
    try {
        // Start the POST request to send the message
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            // here the message does not matter
            body: JSON.stringify({ 'message': userInput, 'mode': mode})
        }).then(response => response.json()).then(data => {
            // Handle the JSON data
            if ("message" in data){
                // execution done
                appendMessage("Execution Done", 'bot-message');
                // enable end of the task
                document.getElementById('submit_button').disabled = false;
            }
            else{
                predicted_action = data['tool_name'];
                default_input = data['tool_input'];
                // console.log(predicted_action);
                // console.log(default_input);
                record_user_action(action="action_prediction", action_input={'message': userInput, 'mode': mode, 'tool_name': predicted_action, 'tool_input': default_input})
                // remove the jumping dots before we append message
                // removeElementwithID('jumping_dots');
                // appendMessage(data['log'], 'bot-message');
                if (predicted_action === "Agent Finish"){
                    // When LLM Agent fails to predict one action, we directly send message
                    appendMessage(data['log'], 'bot-message');
                }
                else{
                    appendActionCard(predicted_action, default_input);
                }
            }
        });
        // .catch(error => console.error(error));
    } catch (error) {
        console.error('Error:', error);
    } finally {
        removeElementwithID('jumping_dots');
        // ensure the action is recorded
        if (!task_done){
            add_button_before_execution();
        }
        after_execution = false;
    }
}

function appendActionCard(selected_action, default_input){
    let form = document.createElement('div');
    form.setAttribute('class', 'message action-message');
    // let form = document.getElementById("chatArea");
    message_list.push({"event": "action_card", "action": selected_action, "parameters": default_input});

    let form_span = document.createElement('div');
    form_span.setAttribute('class', 'input-group mb-3');

    // put tool name at the top of form
    let span = document.createElement('span');
    span.setAttribute("class", 'input-group-text form-control');
    span.innerText = selected_action;
    form_span.appendChild(span);
    form.appendChild(form_span);


    let index = -1;

    for (let i = 0; i < action_list.length; i++){
        if (action_list[i]["tool_name"] === selected_action){
            index = i;
            break;
        }
    }

    // create tool input form elements
    // console.log(index);
    // console.log(selected_action);
    // console.log(action_list);
    let args = action_list[index]["schema"];
    // console.log(args);
    for ( let parameter_name in args){
        format_dict = args[parameter_name];
        if (parameter_name === 'user_id'){
            continue;
            // ignore user_id in the parameters
        }
        format_dict = args[parameter_name];
        title = format_dict["title"]
        description = format_dict["description"]
        type = format_dict["type"]
        // let flag = (use_default && selected_action === predicted_action);
        // console.log(parameter_name);
        // console.log(flag);
        // if (flag){
        default_value = default_input[parameter_name]
        // }
        let newelement = document.createElement('div');
        newelement.setAttribute('class', 'input-group mb-3');
        let span_ = document.createElement('span');
        span_.setAttribute("class", 'input-group-text');
        span_.innerText = title;
        newelement.appendChild(span_);
        if ('enum' in format_dict) {
            // string input with a given range
            // console.log("enum exist, create select element");
            enum_list = format_dict['enum'];
            let select = document.createElement('select');
            // select.setAttribute("id", "action-form-" + title);
            select.setAttribute("class", "form-select");
            for (var i = 0; i < enum_list.length ; i++ ){
                var option = document.createElement('option');
                option.value = enum_list[i];
                option.text  = enum_list[i];
                if (default_value === enum_list[i]){
                    option.setAttribute('selected', true)
                }
                select.appendChild(option);
            }
            select.disabled = true;
            newelement.appendChild(select);
        } else if (type === 'string') {
            var input_string = document.createElement('input');
            // input_string.setAttribute('id', "action-form-" + title);
            input_string.setAttribute('type', 'text');
            input_string.setAttribute("class", "form-control");
            // if (flag){
            input_string.value = default_value;
            // }
            input_string.setAttribute('placeholder', description);
            input_string.disabled = true;
            newelement.appendChild(input_string);
        }
        else {
            // console.log("create input element for number")
            // integer case, we can get min and max from args
            var input_number = document.createElement('input');
            // input_number.setAttribute('id', "action-form-" + title);
            input_number.setAttribute('type', 'number');
            input_number.setAttribute("class", "form-control");
            // if there is a range for number, setup the range
            if ('minimum' in format_dict){
                input_number.setAttribute('min', format_dict['minimum']);
            }
            if ('maximum' in format_dict){
                input_number.setAttribute('max', format_dict['maximum']);
            }
            // if (flag){
            // input_number.value = default_value;
            // }
            if (default_value === null){
                // when prediction is null, fill in default number
                if ('default' in format_dict){
                    input_number.value = format_dict['default'];
                }
            }
            else {
                // when the predicted parameter is not null
                input_number.value = default_value;
            }
            // shall we add min / max here?
            input_number.setAttribute('placeholder', description);
            // console.log(newelement)
            input_number.disabled = true;
            newelement.appendChild(input_number);
        }
        form.appendChild(newelement);
    }
    // append the action card to messages
    document.getElementById('messages').appendChild(form);
}


// question: shall we move the non-async part outside?
// async function one_step(userInput) {
//     // Then show agent execution output
//     try {
//         // Start the POST request to send the message
//         const response = await fetch('/planning_agent/one_step', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json'
//             },
//             body: JSON.stringify({ message: userInput })
//         });

//         let reader = response.body.getReader();
//         let decoder = new TextDecoder();

//         // Create a container for the bot's message
//         let botMessageContainer = createMessageContainer('bot-message');

//         while (true) {
//             const { value, done } = await reader.read();
//             if (done) break;
//             let chunk = decoder.decode(value, { stream: true });
//             // Replace newline characters with HTML <br> tags
//             chunk = chunk.replace(/[/\n]+/g, '<br>');
//             chunk = chunk.replace(/\n/g, '<br>');
//             // To-do, ensure the plan step is correctly transferred to new line
//             // ensure \t or space is kept in the message
//             botMessageContainer.innerHTML += chunk;
//         }
//         // Scroll the bot's message container into view
//         botMessageContainer.scrollIntoView({ behavior: 'smooth' });
//     } catch (error) {
//         console.error('Error:', error);
//     } finally {
//         if (!task_done){
//             add_button(before_execution=false);
//         }
//     }
// }

function appendForm(selected_action, use_default = false) {
    let form = document.createElement('div');
    form.setAttribute('class', 'message action-message');
    // let form = document.getElementById("chatArea");
    message_list.push({"event": "action_card_specification", "action": selected_action});

    let form_span = document.createElement('div');
    form_span.setAttribute('class', 'input-group mb-3');

    // put tool name at the top of form
    let span = document.createElement('span');
    span.setAttribute("class", 'input-group-text form-control');
    span.innerText = selected_action;
    form_span.appendChild(span);
    form.appendChild(form_span);


    let index = -1;

    for (let i = 0; i < action_list.length; i++){
        if (action_list[i]["tool_name"] === selected_action){
            index = i;
            break;
        }
    }

    // create tool input form elements
    // console.log(index);
    let args = action_list[index]["schema"];
    // console.log(args);
    for ( let parameter_name in args){
        format_dict = args[parameter_name];
        if (parameter_name === 'user_id'){
            continue;
            // ignore user_id in the parameters
        }
        format_dict = args[parameter_name];
        title = format_dict["title"]
        description = format_dict["description"]
        type = format_dict["type"]
        let flag = (use_default && selected_action === predicted_action);
        // console.log(parameter_name);
        // console.log(flag);
        if (flag){
            default_value = default_input[parameter_name]
        }
        let newelement = document.createElement('div');
        newelement.setAttribute('class', 'input-group mb-3');
        let span_ = document.createElement('span');
        span_.setAttribute("class", 'input-group-text');
        span_.innerText = title;
        newelement.appendChild(span_);
        if ('enum' in format_dict) {
            // string input with a given range
            // console.log("enum exist, create select element");
            enum_list = format_dict['enum'];
            let select = document.createElement('select');
            select.setAttribute("id", "action-form-" + title);
            select.setAttribute("class", "form-select");
            for (var i = 0; i < enum_list.length ; i++ ){
                var option = document.createElement('option');
                option.value = enum_list[i];
                option.text  = enum_list[i];
                if (flag && default_value === enum_list[i]){
                    option.setAttribute('selected', true)
                }
                select.appendChild(option);
            }
            newelement.appendChild(select);
        } else if (type === 'string') {
            var input_string = document.createElement('input');
            input_string.setAttribute('id', "action-form-" + title);
            input_string.setAttribute('type', 'text');
            input_string.setAttribute("class", "form-control");
            if (flag){
                input_string.value = default_value;
            }
            input_string.setAttribute('placeholder', description);
            newelement.appendChild(input_string);
        }
        else {
            // console.log("create input element for number")
            // integer case, we can get min and max from args
            var input_number = document.createElement('input');
            input_number.setAttribute('id', "action-form-" + title);
            input_number.setAttribute('type', 'number');
            input_number.setAttribute("class", "form-control");
            // if there is a range for number, setup the range
            if ('minimum' in format_dict){
                input_number.setAttribute('min', format_dict['minimum']);
            }
            if ('maximum' in format_dict){
                input_number.setAttribute('max', format_dict['maximum']);
            }
            if (default_value === null){
                // when prediction is null, fill in default number
                if ('default' in format_dict){
                    input_number.value = format_dict['default'];
                }
            }
            else {
                // when the predicted parameter is not null
                if (flag){
                    input_number.value = default_value;
                }
            }
            // if (flag){
            //     input_number.value = default_value;
            // }
            // shall we add min / max here?
            input_number.setAttribute('placeholder', description);
            // console.log(newelement)
            newelement.appendChild(input_number);
        }
        form.appendChild(newelement);
        // if (type === 'string'){
        //     // string input, not specified, to check
        //     var newelement = document.createElement('input');
        //     newelement.setAttribute('id', title);
        //     newelement.setAttribute('type', 'text');
        //     newelement.setAttribute('placeholder', description);
        // } 
    }

    document.getElementById('messages').appendChild(form);
    
    let ExecuteBtn = document.createElement('button');
    ExecuteBtn.textContent = 'Execute';
    // addBtn.className = 'insert-btn';
    ExecuteBtn.setAttribute('id', 'ExecuteBtn');
    ExecuteBtn.setAttribute('class', 'btn btn-primary');
    ExecuteBtn.addEventListener('click', function(){
        // console.log("button Execute clicked");
        removeElementwithID('ExecuteBtn');
        // to check whether we should formulate a string for user-specified action
        appendMessage('Execute', 'user-message');
        // continue execute one step further

        let tool_input = {};
        for ( let parameter_name in args){
            if (parameter_name === 'user_id' && 'user_id' in default_input){
                tool_input['user_id'] = default_input['user_id']
                continue;
                // ignore user_id in the parameters
            }
            format_dict = args[parameter_name];
            title = "action-form-" + format_dict["title"]
            description = format_dict["description"]
            type = format_dict["type"]
            if ('enum' in format_dict){
                // select type of input
                value = document.getElementById(title).value.trim();
            } else {
                // integer
                value = document.getElementById(title).value;
            }
            document.getElementById(title).disabled = true;
            tool_input[parameter_name] = value;
        }

        action_execution(tool_name=selected_action, tool_input=tool_input);
    });

    form.appendChild(ExecuteBtn);
    // actionForm.scrollIntoView({ behavior: 'smooth' });
}

function appendactionSelect() {
    let default_action = predicted_action;
    message_list.push({"event": "action_select"});

    appendMessage("Please choose one action to execute", 'bot-message');

    let tp_div = document.createElement('div');
    tp_div.setAttribute("class", "input-group mb-3");
    let select = document.createElement('select');
    select.setAttribute("id", "actionSelect");
    select.setAttribute("class", "form-select");
    for (var i = 0; i < action_list.length ; i++ ){
        var action = document.createElement('option');
        action.value = action_list[i]["tool_name"];
        action.text  = action_list[i]["tool_name"];
        // select the default action
        if (default_action === action_list[i]["tool_name"]){
            action.setAttribute("selected", true);
        }
        select.appendChild(action);
    }
    tp_div.appendChild(select);
    // select.scrollIntoView({ behavior: 'smooth' });

    let confirmBtn = document.createElement('button');
    confirmBtn.textContent = 'Confirm';
    confirmBtn.setAttribute('id', 'confirmBtn');
    confirmBtn.addEventListener('click', function(){
        // console.log("button Confirm clicked");

        // get selected action
        var select = document.getElementById('actionSelect');
        let selected_action = select.value;

        removeElementwithID('actionSelect');
        removeElementwithID('confirmBtn');
        // after one action selected, remove the action selection and the confirm button? shall we keep it
        if (selected_action === default_action){
            appendForm(selected_action, use_default=true);
        }
        else{
            appendForm(selected_action, use_default=false);
        }
    });
    tp_div.appendChild(confirmBtn);

    document.getElementById('messages').appendChild(tp_div);
}

function appendMessage(text, className) {
    let messageContainer = createMessageContainer(className);
    messageContainer.innerHTML = text.replace(/\n/g, '<br>'); // Replace newlines with <br>
    document.getElementById('messages').appendChild(messageContainer);
    messageContainer.scrollIntoView({ behavior: 'smooth' });

    message_list.push({"text": text, "class": className})
}

function createMessageContainer(className) {
    let div = document.createElement('div');
    div.classList.add('message', className);
    document.getElementById('messages').appendChild(div);
    return div;
}

function add_button_attention_check(){
    // In attention check, we give three buttons, and ask users to choose one among them
    document.getElementById('userInput').disabled = true;
    document.getElementById('userInput').setAttribute('placeholder', 'Input disabled, choose one button under the new message');
    document.getElementById('send_button').disabled = true;
    // disable user input and send button before user choose one mode of response
    let addBtn = document.createElement('button');
    addBtn.textContent = 'Proceed';
    // addBtn.className = 'insert-btn';
    addBtn.setAttribute('id', 'addBtn');
    addBtn.addEventListener('click', function(){
        // console.log("button Proceed clicked");
        removeElementwithID('addBtn');
        // action specification only appear before execution
        removeElementwithID('actionBtn');
        removeElementwithID('reflectionBtn');
        appendMessage('You clicked button Proceed. Unfortunately, you failed one attention check here. Please move forward', 'user-message');
        record_user_action(action="attention_check", action_input={"button": "Proceed"});
        attention_check_flag = false;
        // after attention check, come back to next step of prediction
        action_prediction(userInput="None", mode="prediction");
    });

    let reflectionBtn = document.createElement('button');
    reflectionBtn.textContent = 'Feedback';
    reflectionBtn.setAttribute('id', 'reflectionBtn');
    // reflectionBtn.className = 'insert-btn';
    reflectionBtn.addEventListener('click', function(){
        // console.log("button Reflection clicked");
        removeElementwithID('addBtn');
        removeElementwithID('reflectionBtn');
        removeElementwithID('actionBtn');
        // after users choose reflection, users can send message again to server
        appendMessage("You clicked button Feedback. Please move forward", 'bot-message');
        record_user_action(action="attention_check", action_input={"button": "Reflection"});
        attention_check_flag = false;
        // after attention check, come back to next step of prediction
        action_prediction(userInput="None", mode="prediction");
    });

    document.getElementById('messages').appendChild(addBtn);
    document.getElementById('messages').appendChild(reflectionBtn);

    let actionBtn = document.createElement('button');
    actionBtn.textContent = 'Specify Action';
    actionBtn.setAttribute('id', 'actionBtn');
    // reflectionBtn.className = 'insert-btn';
    actionBtn.addEventListener('click', function(){
        // console.log("button action clicked");

        // get current 
        removeElementwithID('addBtn');
        removeElementwithID('reflectionBtn');
        removeElementwithID('actionBtn');
        // after one button clicked, users are able to input again
        appendMessage("You clicked button Specify Action. Unfortunately, you failed one attention check here. Please move forward", 'bot-message');
        record_user_action(action="attention_check", action_input={"button": "Specify Action"});
        attention_check_flag = false;
        // after attention check, come back to next step of prediction
        action_prediction(userInput="None", mode="prediction");
    });
    document.getElementById('messages').appendChild(actionBtn);
}

function add_button_after_execution(){
    document.getElementById('userInput').disabled = true;
    document.getElementById('userInput').setAttribute('placeholder', 'Input disabled, choose one button under the new message');
    document.getElementById('send_button').disabled = true;
    // disable user input and send button before user choose one mode of response
    let addBtn = document.createElement('button');
    addBtn.textContent = 'Next Step';
    // addBtn.className = 'insert-btn';
    addBtn.setAttribute('id', 'addBtn');
    addBtn.addEventListener('click', async function(){
        // console.log("button Proceed clicked");
        removeElementwithID('addBtn');
        appendMessage('Okay, let us move forward to next Step', 'user-message');
        record_user_action(action="Next Step", action_input={});
        // continue execute one step further
        await append_cur_step(start_status = false);
        // show attention check after a given step, now we take the first step by default
        if (!attention_check_flag){
            action_prediction(userInput="None", mode="prediction");
        }
        else{
            attention_check(userInput="None", mode="prediction")
        }
    });

    document.getElementById('messages').appendChild(addBtn);
}

function add_button_before_execution() {
    document.getElementById('userInput').disabled = true;
    document.getElementById('userInput').setAttribute('placeholder', 'Input disabled, choose one button under the new message');
    document.getElementById('send_button').disabled = true;
    // disable user input and send button before user choose one mode of response
    let addBtn = document.createElement('button');
    addBtn.textContent = 'Proceed';
    // addBtn.className = 'insert-btn';
    addBtn.setAttribute('id', 'addBtn');
    addBtn.addEventListener('click', function(){
        // console.log("button Proceed clicked");
        removeElementwithID('addBtn');
        record_user_action(action="Proceed", action_input={});
        appendMessage('Okay, let us execute the above action', 'user-message');
        // continue execute one step further
        action_execution(tool_name=predicted_action, tool_input=default_input);
    });

    document.getElementById('messages').appendChild(addBtn);

}

function removeElementwithID(id) {
    const taskItem = document.getElementById(id);
    taskItem.parentNode.removeChild(taskItem);
}