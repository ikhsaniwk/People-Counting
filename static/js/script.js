// static/js/script.js
async function updateStats() {
    try {
        const res = await fetch('/stats', {cache: 'no-store'});
        if (!res.ok) throw new Error('Bad response');

        const data = await res.json();
        document.getElementById("inCount").innerText = data.in_count || 0;
        document.getElementById("outCount").innerText = data.out_count || 0;
        document.getElementById("fps").innerText = (data.fps || 0).toFixed(1);

        const statusElem = document.getElementById("status");
        if (data.running) {
            statusElem.innerText = "Status: Running";
            statusElem.style.color = "green";
        } else {
            statusElem.innerText = "Status: Stopped";
            statusElem.style.color = "red";
        }
    } catch (err) {
        console.error("Error fetching stats:", err);
        // show stopped if error
        const statusElem = document.getElementById("status");
        statusElem.innerText = "Status: Disconnected";
        statusElem.style.color = "orange";
    }
}

// Buttons wiring
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('btnStart').addEventListener('click', async () => {
        try {
            const res = await fetch('/start', {method: 'POST'});
            const data = await res.json();
            console.log("Start:", data);
        } catch (e) { console.error(e); }
    });

    document.getElementById('btnStop').addEventListener('click', async () => {
        try {
            const res = await fetch('/stop', {method: 'POST'});
            const data = await res.json();
            console.log("Stop:", data);
        } catch (e) { console.error(e); }
    });

    document.getElementById('btnReset').addEventListener('click', async () => {
        try {
            const res = await fetch('/reset', {method: 'POST'});
            const data = await res.json();
            console.log("Reset:", data);
            // clear local display immediately
            document.getElementById("inCount").innerText = 0;
            document.getElementById("outCount").innerText = 0;
        } catch (e) { console.error(e); }
    });

    // start polling
    updateStats();
    setInterval(updateStats, 500); // 500 ms
});

document.addEventListener('DOMContentLoaded', () => {
    // Event existing
    document.getElementById('btnStart').addEventListener('click', async () => {
        await fetch('/start', {method: 'POST'});
        updateStats();
    });

    document.getElementById('btnStop').addEventListener('click', async () => {
        await fetch('/stop', {method: 'POST'});
        updateStats();
    });

    document.getElementById('btnReset').addEventListener('click', async () => {
        await fetch('/reset', {method: 'POST'});
        updateStats();
        document.getElementById("inCount").innerText = 0;
        document.getElementById("outCount").innerText = 0;
    });

    // Tombol Dashboard
    document.getElementById('btnDashboard').addEventListener('click', () => {
        window.location.href = '/dashboard'; // arahkan ke halaman baru
    });

    // Start polling
    updateStats();
    setInterval(updateStats, 500);
});

