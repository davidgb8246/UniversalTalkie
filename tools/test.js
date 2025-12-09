/*


*/

class SecureWS {
    constructor(url, passkey) {
        this.url = url;
        this.passkey = passkey;
        this.ws = null;

        // Message handlers map
        this.handlers = {};
    }

    connect() {
        console.log("Connecting to", this.url);

        // Create WebSocket using passkey as subprotocol
        this.ws = new WebSocket(this.url, this.passkey);

        this.ws.onopen = () => {
            console.log("Connected to secure WebSocket server.");
        };

        this.ws.onerror = () => {
            console.error("WebSocket error – authentication failed or connection issue.");
        };

        this.ws.onclose = (event) => {
            if (event.code === 1006) {
                console.error("Disconnected: likely invalid passkey.");
            } else {
                console.log("Connection closed:", event.code, event.reason);
            }
        };

        this.ws.onmessage = (event) => {
            this.handleMessage(event.data);
        };
    }

    // Register message handlers ("type": function)
    on(type, callback) {
        this.handlers[type] = callback;
    }

    // Send JSON safely
    send(type, payload = {}) {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, ...payload }));
        } else {
            console.warn("WebSocket not open. Cannot send:", type);
        }
    }

    // Dispatch incoming messages
    handleMessage(raw) {
        try {
            const msg = JSON.parse(raw);

            if (!msg.type) {
                console.warn("Received message without type:", msg);
                return;
            }

            const handler = this.handlers[msg.type];
            if (handler) {
                handler(msg);
            } else {
                console.warn("No handler for message type:", msg.type);
            }
        } catch (err) {
            console.error("Invalid JSON from server:", raw);
        }
    }
}

const ws = new SecureWS("wss://universaltalkie.davidgb.net/ws/", "73a282ee3c390e8284b80a41ba7932b7");
ws.connect(); 

