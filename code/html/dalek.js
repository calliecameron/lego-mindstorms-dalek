$(document).ready(function() {
    var ws = new WebSocket("ws://" + window.location.hostname + ":12346");

    $("#foobar").click(function() {
        console.log("SEND");
        ws.send("playsound:exterminate");
    })

    ws.onmessage = function(event) {
        console.log(event);
    }
});
