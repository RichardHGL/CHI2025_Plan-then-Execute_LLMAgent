    // initialize one array from flask render variable tp_plan
    var task_list_hierachy = {{ tp_plan | tojson }};
    console.log(task_list_hierachy);

    function searchTask(cur_index) {
        for(var i=0; i<task_list_hierachy.length ; i++){
            if(task_list_hierachy[i].index === cur_index){
                return i;
            }
        }
        return -1;
    }

    function searchInsearchPosition(prefix, prefix_pos) {
        var last_index = prefix_pos;
        for(var i=prefix_pos; i<task_list_hierachy.length ; i++){
            if(task_list_hierachy[i].index.startsWith(prefix)){
                last_index = i;
            }
        }
        return task_list_hierachy[last_index].index;
    }

    function new_step_li(new_index){
        // create one new task step object
        const li = document.createElement('li');
        li.className = 'input-group mb-3';
        const level = get_index_level(new_index)
        li.setAttribute('data-level', level);
        li.setAttribute('id', new_index);

        // insert the object into the position
        const input = document.createElement('input');
        input.type = 'text';
        input.className = "form-control";
        input.value = "";

        const para = document.createElement('span');
        para.setAttribute('id', "p-" + new_index);
        para.className = "input-group-text";
        const node = document.createTextNode(new_index);
        para.append(node)

        // const addBtn = document.createElement('button');
        // addBtn.textContent = 'Add one step';
        // addBtn.className = 'insert-btn';
        // addBtn.addEventListener('click', function(){
        //     addstep(new_index);
        // });

        // const insertBtn = document.createElement('button');
        // insertBtn.textContent = 'Insert Before';
        // insertBtn.className = 'insert-btn';
        // insertBtn.addEventListener('click', function(){
        //     insertTask(new_index, "before");
        // });

        // const insertBtn2 = document.createElement('button');
        // insertBtn2.textContent = 'Insert Behind';
        // insertBtn2.className = 'insert-btn';
        // insertBtn2.addEventListener('click', function(){
        //     insertTask(new_index, "behind");
        // });

        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Delete Step';
        deleteBtn.className = 'btn btn-warning';
        deleteBtn.addEventListener('click', function(){
            deleteTask(this.parentNode.getAttribute('id'));
        });

        li.appendChild(para);
        li.appendChild(input);
        // li.appendChild(addBtn);
        // li.appendChild(insertBtn);
        // li.appendChild(insertBtn2);
        li.appendChild(deleteBtn);
        return li;
    }

    function get_index_level(tp_index){
        const index_list = tp_index.split('.');
        if (index_list.length == 3){
            return 3;
        }
        else{
            if (tp_index[tp_index.length-1] === '.'){
                return 1;
            }
            else{
                return 2;
            }
        }
    }

    function get_three_levels(tp_index){
        const index_list = tp_index.split('.');
        var number_1 = -1;
        var number_2 = -1;
        var number_3 = -1;
        if (index_list.length == 3){
            number_1 = parseInt(index_list[0]);
            number_2 = parseInt(index_list[1]);
            number_3 = parseInt(index_list[2]);
        }
        else{
            if (tp_index[tp_index.length-1] === '.'){
                number_1 = parseInt(index_list[0]);
            }
            else{
                number_1 = parseInt(index_list[0]);
                number_2 = parseInt(index_list[1]);
            }
        }
        return [number_1, number_2, number_3]
    }

    function update_single_index(cur_index, new_index, level, mode){
        // add 1.2.3, then it only affect 1.2.x where w >= 3
        // delete 1.2.3 then it only affect 1.2.x where w >= 3
        // add 1.2 then it only affect 1.x where x >= 2
        // add 1. then it affect x. where x >= 1
        const three_levels_base = get_three_levels(new_index);
        const three_levels = get_three_levels(cur_index);
        for (let i = 0; i < level-1; i++) {
            if (three_levels[i] != three_levels_base[i]){
                return [false, null];
            }
        }
        if (mode == "delete"){
            three_levels[level - 1] = three_levels[level - 1] - 1;
        }
        else{
            if (three_levels[level - 1] != -1){
                if (three_levels[level - 1] < three_levels_base[level - 1]){
                    return [false, null]
                }
                three_levels[level - 1] = three_levels[level - 1] + 1;
            }
            else{
                return [false, null]
            }
        }
        var new_index = three_levels[0].toString()
        if (three_levels[1] == -1){
            return [true, new_index + "."];
        }
        for(var i=1; i<three_levels.length ; i++){
            if(three_levels[i] != -1){
                new_index = new_index + "." + three_levels[i].toString()
            }
        }
        return [true, new_index];
    }

    function update_planning_index(cur_index, target_index, cur_index_in_array, mode){
        // cur_index: the current index of element where we trigger add or delete button
        // new_index: the inserted step index or deleted step index
        // the current index (cur_index) in the task_list_hierachy
        // mode in ["before", "behind", "delete"]
        const level = get_index_level(target_index)
        const starting_index = cur_index_in_array;
        if (mode === "delete"){
            const starting_index = cur_index_in_array;
            for (let i = starting_index; i < task_list_hierachy.length; i++) {
                const old_index = task_list_hierachy[i].index;
                const [update_flag, new_index] = update_single_index(old_index, target_index, level, mode);
                console.log(old_index, update_flag, new_index)
                if (update_flag){
                    // update the array task_list_hierachy index
                    task_list_hierachy[i].index = new_index
                    // update the html element id and index in <p>
                    const taskItem = document.getElementById(old_index);
                    taskItem.setAttribute("id", new_index)
                    const taskItem_p = document.getElementById("p-" + old_index);
                    taskItem_p.innerText = new_index
                    taskItem_p.setAttribute("id", "p-" + new_index)
                    // To-do: update the function associated with every button
                }
            }
        }
        else{
            //for adding step, update the step index from the last to current index
            if (mode === "behind"){
                // delete current item, update the index starting from next step
                const starting_index = cur_index_in_array + 1;
            }
            else if (mode === "before"){
                // starting from the current step
                const starting_index = cur_index_in_array;
            }
            for (let i = task_list_hierachy.length - 1; i >= starting_index; i--) {
                const old_index = task_list_hierachy[i].index;
                const [update_flag, new_index] = update_single_index(old_index, target_index, level, mode);
                console.log(i, old_index, update_flag, new_index)
                if (update_flag){
                    // update the array task_list_hierachy index
                    task_list_hierachy[i].index = new_index
                    // update the html element id and index in <p>
                    const taskItem = document.getElementById(old_index);
                    taskItem.setAttribute("id", new_index)
                    const taskItem_p = document.getElementById("p-" + old_index);
                    taskItem_p.innerText = new_index
                    taskItem_p.setAttribute("id", "p-" + new_index)
                    // To-do: update the function associated with every button
                }
            }
        }

    }

    function validate_new_index(new_index){
        if (new_index.includes(".")){
            const index_list = new_index.split('.');
            if (index_list.length > 3){
                return false
            }
            if (new_index.endsWith(".")){
                //x.
                if (isNaN(Number(index_list[0], 10))){
                    return false;
                }
            }
            else{
                //x.y or x.y.z
                for(let i=0; i < index_list.length; i ++){
                    if (isNaN(Number(index_list[i], 10))){
                        return false;
                    }
                }
            }
            return true;
        }
        else{
            return false;
        }
    }

    function addOneStep(){
        const new_index = prompt('Enter the new step index, valid index up to three levels e.g., x. or x.y or x.y.z\nIt is also possible to add one step with same index as current plan, then the steps behind it will be automatically re-indexed\n')
        if (new_index){
            // first confirm the string is in the format of x.y.z or x.y or x.
            if (validate_new_index(new_index)){
                // search for a exact place to insert the new element
                last_index = task_list_hierachy[task_list_hierachy.length - 1].index;
                first_index = task_list_hierachy[0].index;
                exact_match = searchTask(new_index);
                if (exact_match == -1){
                    const level = get_index_level(new_index);
                    const number_list = get_three_levels(new_index);
                    if (level == 1){
                        // insert x. which x. does not exist in current plan, ensure x-1. exist
                        prefix = (number_list[0] - 1).toString() + "."
                        prefix_match = searchTask(prefix);
                        if (prefix_match == -1){
                            console.log("aleter prefix", prefix)
                            alert("The new index "+new_index+ " is invalid, as its prefix "+ prefix + " does not exist.")
                        }
                        else{
                            // search for the last step which contains the prefix
                            index_to_insert = searchInsearchPosition(prefix, prefix_match)
                            insertTask(index_to_insert, new_index, mode="behind");
                        }
                    }
                    else{
                        if (number_list[level - 1] == 1){
                            // a new sub-step, ensure the parent of it exists
                            if (level == 2){
                                // x.1, and x.1 does not exist, ensure x. exist
                                prefix = number_list[0].toString() + "."
                            }
                            else{
                                //x.y.1, and x.y.1 does not exist, ensure x.y exist
                                prefix = number_list[0].toString() + "." + number_list[1].toString()
                            }
                        }
                        else{
                            if (level == 2){
                                //x.y (y!=1)
                                prefix = number_list[0].toString() + "." + (number_list[1]-1).toString()
                            }
                            else{
                                // x.y.z (z != 1)
                                prefix = number_list[0].toString() + "." + number_list[1].toString() + "." + (number_list[2]-1).toString()
                            }
                        }
                        prefix_match = searchTask(prefix);
                        if (prefix_match == -1){
                            console.log("aleter prefix", prefix)
                            alert("The new index "+new_index+ " is invalid, as its prefix "+ prefix + " does not exist.")
                        }
                        else{
                            // search for the last step which contains the prefix
                            index_to_insert = searchInsearchPosition(prefix, prefix_match)
                            insertTask(index_to_insert, new_index, mode="behind")
                        }
                    }
                }
                else{
                    // if we find an exact match, insert before the exact match
                    insertTask(new_index, new_index, mode="before");
                }
            }
            else{
                alert("Invalid index " + new_index)
            }
        }
    }

    function updateplan(){
        console.log("Planning updated")
        //Fetch the input from the user interface and send to the server
        for (let i=0; i< task_list_hierachy.length; i++){
            const cur_index = task_list_hierachy[i].index
            const taskItem = document.getElementById(cur_index);
            task_list_hierachy[i].step = taskItem.querySelector("input").value;
        }
        data = {
            "plan": task_list_hierachy
        };
        $.post({url: "/planning_agent/updateplan", type: "POST", data: JSON.stringify(data), {#dataType:'json'#}
                contentType: "application/json; charset=UTF-8",})
    }

    function insertTask(cur_index, new_index, mode) {
        //locate current item with id
        const taskItem = document.getElementById(cur_index);
        console.log("insertTask", cur_index);
        const index_list = cur_index.split('.');
        const level = get_index_level(new_index);

        // search current position in the json array
        const cur_index_in_array = searchTask(cur_index);
        // insert an empty step, with 
        var new_step = {
            "step": "",
            "index": new_index,
            "data_level": level,
            "tool": "null"
        }
        const new_taskItem = new_step_li(new_index);

        update_planning_index(cur_index, new_index, cur_index_in_array, mode)

        // insert the new step
        if (mode === "before"){
            // insert before current item
            task_list_hierachy.splice(cur_index_in_array, 0, new_step);
            // insert the new element before the current task step
            taskItem.parentNode.insertBefore(new_taskItem, taskItem);
        }
        else{
            // insert at next position
            task_list_hierachy.splice(cur_index_in_array + 1, 0, new_step);
            // insert the new element before the next sibling of the current task step
            taskItem.parentNode.insertBefore(new_taskItem, taskItem.nextSibling);
        }
        console.log(task_list_hierachy);

        // To-do: update the index of items in the array
    }

    function deleteTask(cur_index) {
        if (window.confirm("Do you really want to delete step " + cur_index + " ?" + "\nThis will totally delete the step and all sub-steps.")) {
            // const taskItem = this.closest('.task-item');
            const taskItem = document.getElementById(cur_index);
            // const cur_index = taskItem.getAttribute('data-index');
            const cur_index_in_array = searchTask(cur_index);
            // console.log(cur_index, typeof(cur_index))
            // console.log(cur_index_in_array);
            // console.log(taskItem);
            // remove one json object from current step?
            // or we should remove all sub-steps? To check
            // console.log(cur_index, cur_index, cur_index_in_array)
            var number_to_delete = 1;
            var index_to_delete = [];
            // check how many sub-steps to delete
            for (let i=cur_index_in_array+1; i < task_list_hierachy.length; i++){
                if (task_list_hierachy[i].index.startsWith(cur_index)){
                    number_to_delete = number_to_delete + 1;
                    index_to_delete.push(task_list_hierachy[i].index);
                }
                else{
                    break;
                }
            }
            // delete the variable list first
            task_list_hierachy.splice(cur_index_in_array, number_to_delete);
            update_planning_index(cur_index, cur_index, cur_index_in_array, mode="delete")
            // console.log("update index done")
            // console.log(task_list_hierachy)
            // task_list_hierachy.splice(cur_index_in_array, number_to_delete);
            taskItem.parentNode.removeChild(taskItem);
            // delete the sub-steps of the current step
            if (index_to_delete.length > 0){
                for (let i = 0; i < index_to_delete.length; i++){
                    const tp_item = document.getElementById(index_to_delete[i]);
                    tp_item.parentNode.removeChild(tp_item);
                }
            }
        }
    }