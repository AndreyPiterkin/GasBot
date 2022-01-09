module.exports = {
    execute(message, args) {
        const fs = require('fs')
        fs.readFile('./subscribed-users.json', 'utf8', function readFileCallback(err, data){
            if (err){
                console.log(err);
            } else {
                obj = JSON.parse(data); //now it's an object
                for(let i = 0; i < obj.user_table.length; i++) {
                    if(obj.user_table[i].id === message.author.id) {
                        obj.user_table[i].started = args[0]
                        obj.user_table[i].low = args[1]
                    }
                }
                json = JSON.stringify(obj); //convert it back to json
                fs.writeFile('./subscribed-users.json', json, 'utf8', () => {
                    message.channel.send(args[2])
                }); 
            }
        });
    }
}