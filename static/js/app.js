// // Connect to the Socket.IO server
var socket = io.connect('http://localhost:5000');
var sl=window.location.protocol + "//" + document.domain + ":" + location.port

// // Handle Socket.IO connection event
socket.on('connect', function () {
    console.log('Connected!', socket.connected);
    console.log(sl);
});



const video = document.querySelector('#videoElement');
var canvas = document.getElementById('canvas');
var context = canvas.getContext('2d');

video.width = 400;
video.height = 300;

if (navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices
        .getUserMedia({ video: true })
        .then(function (stream) {
            video.srcObject = stream;

            video.play();
        })
        .catch(function (error) {
            console.error('Error accessing camera:', error);
        });
}

const FPS = 10;
setInterval(() => {
    width=video.width;
    height=video.height;
    context.drawImage(video, 0, 0, width,height);
    var data = canvas.toDataURL('image/jpeg', 0.5);
    context.clearRect(0, 0, width, height);
    socket.emit('image', data);
}, 1000 / FPS);

setInterval(() => {
    width=video.width;
    height=video.height;
    context.drawImage(video, 0, 0, width,height);
    var data = canvas.toDataURL('image/jpeg', 0.5);
    context.clearRect(0, 0, width, height);
    socket.emit('img', data);
}, 1000 / FPS);

// 
// socket.on('pose_data', function (data) {
//     // Update the UI with the curl counters
//     document.getElementById('left_counter').innerText = data.left_counter;
//     document.getElementById('right_counter').innerText = data.right_counter;

//     // Update the 'photo' element with the processed image
//     var photo = document.getElementById('photo');
//     photo.setAttribute('src',data.frame);
// });

// Update the 'photo' element with the processed image
socket.on('pose_data', function (data) {
    console.log('Received pose data:', data);

    // Update the UI with the curl counters
    document.getElementById('left_counter').innerText = data.left_counter;
    document.getElementById('right_counter').innerText = data.right_counter;

    // Update the 'photo' element with the processed image
    var photo = document.getElementById('photo');
    photo.setAttribute('src',data.frame);
});

socket.on("processed_image", function (image) {
    photo.setAttribute("src", image);
  });
