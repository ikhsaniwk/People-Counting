let trendChart;

async function updateDashboard() {
    try {
        // Ambil data stats
        const statsRes = await fetch('/stats', {cache: 'no-store'});
        const stats = await statsRes.json();

        document.getElementById('inCount').innerText = stats.in_count || 0;
        document.getElementById('outCount').innerText = stats.out_count || 0;
        document.getElementById('totalCount').innerText = (stats.in_count + stats.out_count) || 0;

        // Ambil 50 data terakhir
        const dbRes = await fetch('/db_last?limit=50', {cache:'no-store'});
        const dbData = await dbRes.json();

        // Update table log 10 terakhir
        const tbody = document.querySelector('#logTable tbody');
        tbody.innerHTML = '';
        dbData.slice(0,10).forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${row[0]}</td><td>${row[1]}</td><td>${row[2]}</td>`;
            tbody.appendChild(tr);
        });

        // Update grafik tren
        const labels = dbData.map(d => new Date(d[1]).toLocaleTimeString());
        const inCounts = dbData.map(d => d[2] === 'IN' ? 1 : 0);
        const outCounts = dbData.map(d => d[2] === 'OUT' ? 1 : 0);

        if (!trendChart) {
            const ctx = document.getElementById('trendChart').getContext('2d');
            trendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {label:'IN', data: inCounts, borderColor:'green', fill:true, backgroundColor:'rgba(0,255,0,0.2)'},
                        {label:'OUT', data: outCounts, borderColor:'red', fill:true, backgroundColor:'rgba(255,0,0,0.2)'}
                    ]
                },
                options: {
                    responsive:true,
                    maintainAspectRatio:false,
                    animation: false, // matikan animasi agar ringan
                    scales: {y: {beginAtZero:true}}
                }
            });
        } else {
            trendChart.data.labels = labels;
            trendChart.data.datasets[0].data = inCounts;
            trendChart.data.datasets[1].data = outCounts;
            trendChart.update();
        }

    } catch(err) {
        console.error("Error updating dashboard:", err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateDashboard();
    setInterval(updateDashboard, 1000); // refresh tiap 1 detik
});
