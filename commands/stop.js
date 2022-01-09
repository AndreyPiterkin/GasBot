module.exports = {
    name: 'stop',
    description: "halt the bot's notification system",
    execute(message, args) {
        const dbHandler = require('../dbHandler')
        dbHandler.execute(message, [false, -1, 'Stopped'])
    }
}