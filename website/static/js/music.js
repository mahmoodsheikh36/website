let listening_data = JSON.parse($('#listening_data_plot').dataset.listening_data)
var ctx = $('#listening_data_plot').getContext('2d');
var canvas = $('#listening_data_plot')
ctx.filter = 'none'

let max_value = 0
for (let i = 0; i < listening_data.length; ++i) {
    time_listened = listening_data[i]
    if (time_listened > max_value) {
        max_value = time_listened
    }
}

let width = canvas.width
let height = canvas.height

ctx.beginPath();
ctx.translate(0.5,0.5);
ctx.moveTo(0, height)
for (let i = 0; i < listening_data.length; ++i) {
    let time_listened = listening_data[i]
    let y = (time_listened * height) / max_value
    let x = (width / listening_data.length) * i
    ctx.lineTo(x, height - y)
}
ctx.strokeStyle = '#ff0000';
ctx.lineWidth = 1
ctx.stroke();

/* thats it! no need for fancy math plotting libraries!! who needs those! */
