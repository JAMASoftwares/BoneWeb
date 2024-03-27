// Global variables
client_cpuram = "CpuRam [%]"

// 
$(document).ready(function(){
    var socket = io.connect('http://'+location.hostname+':'+location.port,{ query:{'clientName':client_cpuram,'deviceInfo':deviceInfo }});
    socket.on('cpuram_data', function(msg) {
        $('#cpu_usage').html('CPU: ' + msg.cpu_usage + ' %');
        $('#ram_usage').html('RAM: ' + msg.ram_usage + ' %');
    });
    socket.on('connect', function(msg) {
        socket.emit('cpuram-start', {taskType: 'cpuramData', client_name: client_cpuram,
                                     msg: "Request: Start CPU-RAM usage stream!"})
    });
    socket.on('message', function(msg) {
        console.log(msg);
    });
});