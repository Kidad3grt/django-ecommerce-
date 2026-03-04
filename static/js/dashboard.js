document.addEventListener("DOMContentLoaded", () => {
    function renderChart(canvasId, type, label, labelFn, valueFn, color) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        const url = canvas.dataset.url;
        fetch(url)
            .then(res => res.json())
            .then(data => {
                new Chart(canvas, {
                    type: type,
                    data: {
                        labels: data.map(labelFn),
                        datasets: [{
                            label: label,
                            data: data.map(valueFn),
                            borderColor: color,
                            backgroundColor: color,
                            fill: type === "line" ? false : true
                        }]
                    },
                    options: { responsive: true }
                });
            })
            .catch(err => console.error(`Error loading ${canvasId} chart:`, err));
    }

    // Sales Chart
    renderChart("salesChart", "line", "Sales",
        x => "Month " + x.created_at__month,
        x => x.total,
        "blue");

    // Products Chart
    renderChart("productsChart", "bar", "Units Sold",
        x => x["items__product__name"],
        x => x.total_sold,
        "orange");

    // Users Chart
    renderChart("usersChart", "line", "New Users",
        x => "Month " + x.joined_at__month,
        x => x.total,
        "green");
});
