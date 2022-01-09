module.exports = {
    name: 'start',
    description: "activate the bot's notification system",
    execute(message, args) {
        if(!args.length) {
            message.channel.send('Specify minimum gas price')
            return;
        }
        const dbHandler = require('../dbHandler')
        dbHandler.execute(message, [true, args[0], 'Started'])
    }
}