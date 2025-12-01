// Auto-refresh dashboard data
let autoRefreshInterval;

function loadCurrentPrice() {
    fetch('/api/price/current')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                updateCurrentPrice(data.data);
            }
        })
        .catch(error => console.error('Error fetching current price:', error));
}

function updateCurrentPrice(priceData) {
    document.getElementById('currentPrice').textContent = `₹${priceData.price.toFixed(2)}`;
    
    const changeElement = document.getElementById('priceChange');
    const change = priceData.change || 0;
    const changePercent = priceData.change_percent || 0;
    
    if (change >= 0) {
        changeElement.className = 'badge bg-success';
        changeElement.textContent = `▲ ${change.toFixed(2)} (${changePercent.toFixed(2)}%)`;
    } else {
        changeElement.className = 'badge bg-danger';
        changeElement.textContent = `▼ ${change.toFixed(2)} (${changePercent.toFixed(2)}%)`;
    }
    
    const now = new Date();
    document.getElementById('lastUpdate').textContent = `Last updated: ${now.toLocaleString()}`;
}

function loadRecentPrices() {
    fetch('/api/prices/latest?limit=10')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateRecentPrices(data.data);
                updateStats(data.data);
            }
        })
        .catch(error => console.error('Error fetching recent prices:', error));
}

function updateRecentPrices(prices) {
    const tbody = document.getElementById('recentPrices');
    
    if (prices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">No data available</td></tr>';
        return;
    }
    
    tbody.innerHTML = prices.map(price => {
        const changeClass = (price.change || 0) >= 0 ? 'text-success' : 'text-danger';
        const changeIcon = (price.change || 0) >= 0 ? '▲' : '▼';
        
        return `
            <tr>
                <td>${price.timestamp}</td>
                <td>₹${price.price.toFixed(2)}</td>
                <td class="${changeClass}">${changeIcon} ${price.change ? price.change.toFixed(2) : '--'}</td>
                <td class="${changeClass}">${price.change_percent ? price.change_percent.toFixed(2) + '%' : '--'}</td>
            </tr>
        `;
    }).join('');
}

function updateStats(prices) {
    if (prices.length === 0) return;
    
    document.getElementById('totalRecords').textContent = prices.length;
    
    const priceValues = prices.map(p => p.price);
    const high = Math.max(...priceValues);
    const low = Math.min(...priceValues);
    
    document.getElementById('todayHigh').textContent = `₹${high.toFixed(2)}`;
    document.getElementById('todayLow').textContent = `₹${low.toFixed(2)}`;
}

// Refresh button
document.getElementById('refreshBtn').addEventListener('click', function() {
    this.disabled = true;
    this.textContent = 'Refreshing...';
    
    fetch('/fetch-now')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadCurrentPrice();
                loadRecentPrices();
            }
        })
        .finally(() => {
            this.disabled = false;
            this.textContent = 'Refresh Now';
        });
});

// Initial load
loadCurrentPrice();
loadRecentPrices();

// Auto-refresh every 30 seconds
autoRefreshInterval = setInterval(() => {
    loadRecentPrices();
}, 30000);