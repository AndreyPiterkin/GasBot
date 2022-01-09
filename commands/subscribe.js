module.exports = {
    name: 'subscribe',
    description: "Subscribe to receive low gas price notifications",
    execute(message, args) {
        const fs = require('fs')
        function sub() {
            fs.readFile('./subscribed-users.json', 'utf8', function readFileCallback(err, data){
                if (err){
                    console.log(err);
                } else {
                obj = JSON.parse(data); //now it's an object
                let inTable = false
                for(let i = 0; i < obj.user_table.length; i++) {
                    if(obj.user_table[i].id === message.author.id) {
                        inTable = true
                    }
                }
                if (!inTable) {
                    obj.user_table.push({id: message.author.id, started: false, low: -1}); //add some data
                }
                json = JSON.stringify(obj); //convert it back to json
                fs.writeFile('./subscribed-users.json', json, 'utf8', () => {
                    message.channel.send('Subscribed!')
                }); 
            }});
        }
        sub();
    }
}