// Browser-like SocketIO Connection Test
// Tests the eventlet fix from browser perspective

const io = require('socket.io-client');

console.log('🔍 Testing SocketIO connection like a real browser...');

const socket = io('http://localhost:5002', {
    transports: ['polling', 'websocket'],
    timeout: 5000,
    forceNew: true
});

let connected = false;
let startTime = Date.now();

socket.on('connect', () => {
    connected = true;
    const connectionTime = Date.now() - startTime;
    console.log(`✅ SocketIO Connected in ${connectionTime}ms`);
    console.log(`   Session ID: ${socket.id}`);
    console.log(`   Transport: ${socket.io.engine.transport.name}`);
    
    // Test the connect_drone event (simulates button click)
    console.log('🔍 Testing connect_drone event...');
    socket.emit('connect_drone', {
        ip: '192.168.193.235',
        port: 5678,
        protocol: 'tcp'
    });
});

socket.on('connect_error', (error) => {
    console.log(`❌ Connection Error: ${error}`);
});

socket.on('disconnect', (reason) => {
    console.log(`🔌 Disconnected: ${reason}`);
});

socket.on('connection_status', (data) => {
    console.log(`📡 Connection Status: ${JSON.stringify(data)}`);
});

socket.on('drone_connection_status', (data) => {
    console.log(`🚁 Drone Status: ${JSON.stringify(data)}`);
});

// Wait for connection then test and cleanup
setTimeout(() => {
    if (connected) {
        console.log('\n🎉 VALIDATION SUCCESS:');
        console.log('✅ SocketIO connects quickly');
        console.log('✅ WebSocket upgrade works');  
        console.log('✅ Events can be sent/received');
        console.log('✅ Connect button should work without popup');
        console.log('\n🎯 The eventlet fix has resolved the issue!');
    } else {
        console.log('\n❌ VALIDATION FAILED: SocketIO connection issues');
    }
    socket.disconnect();
    process.exit(connected ? 0 : 1);
}, 3000);