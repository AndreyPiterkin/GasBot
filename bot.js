const Discord = require('discord.js')
const { Client, Intents} = require('discord.js');
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));
const fs = require('fs')
const {token, fetchUrl, fetchCookie, fetchAuthority, prefix} = require('./config.json')

const client = new Client({
    intents: [
        'GUILDS',
        'DIRECT_MESSAGES',
        'GUILD_MESSAGES'
    ],
    partials: ['MESSAGE', 'CHANNEL']
});

client.commands = new Discord.Collection()
const commandFiles = fs.readdirSync('./commands/').filter(file => file.endsWith('.js'));

for (const file of commandFiles) {
    const command = require(`./commands/${file}`);
    client.commands.set(command.name, command);
  }

client.once('ready', () => {
    console.log('Ready!')
})

client.on('messageCreate', message => {
    if(!message.content.startsWith(prefix) || message.author.bot) return;
    const args = message.content.slice(prefix.length).trim().split(' ');
    const command = args.shift().toLowerCase();

    if (command === "subscribe") client.commands.get('subscribe').execute(message, args);
    if (command === "start") client.commands.get('start').execute(message, args);
    if (command === "stop") client.commands.get('stop').execute(message, args);
})

const inter = setInterval(async () => {
    const response = await fetch(fetchUrl, {
        headers: {
            authority: fetchAuthority,
            cookie: fetchCookie
        }
    })

    const res = await response.json()
    const lowBasePrio = res.lowBasePriority
    const lowBasePrioNumber = parseInt(lowBasePrio.substr(6,9))

    fs.readFile('subscribed-users.json', 'utf8', function readFileCallback(err, data){
        if (err){
            console.log(err);
        } else {
            obj = JSON.parse(data); //now it's an object
            for(let i = 0; i < obj.user_table.length; i++) {
                if (obj.user_table[i].started && lowBasePrioNumber <= obj.user_table[i].low) {
                    client.users.fetch(obj.user_table[i].id, false).then((user) => {
                        user.send("Base Gas Price: " + lowBasePrioNumber + " gwei")
                    })
                }
            }
        }
    });
}, 2000)

client.login(token);