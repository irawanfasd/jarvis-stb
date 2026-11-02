#!/usr/bin/env node
/**
 * Kirim pesan ke chat server via Socket.IO.
 * Usage: node /root/jarvis-chat-send.js "pesan" [username]
 */
const { io } = require('/var/www/chat/node_modules/socket.io-client');

const msg = process.argv[2] || 'test dari JARVIS';
const username = process.argv[3] || 'JARVIS';
const URL = process.env.CHAT_URL || 'http://127.0.0.1:3001';

const socket = io(URL, {
    transports: ['websocket'],
    reconnection: false,
    timeout: 5000,
});

const done = (code, note) => {
    if (note) console.log(note);
    try { socket.disconnect(); } catch (e) {}
    process.exit(code);
};

const t = setTimeout(() => done(1, 'timeout'), 8000);

socket.on('connect', () => {
    socket.emit('join', username);
    setTimeout(() => {
        socket.emit('chat message', {
            username: username,
            message: msg,
            image_url: null,
            time: new Date().toLocaleTimeString('id-ID'),
        });
        setTimeout(() => {
            clearTimeout(t);
            done(0, 'sent');
        }, 500);
    }, 300);
});

socket.on('connect_error', (e) => {
    clearTimeout(t);
    done(1, 'connect_error: ' + e.message);
});
