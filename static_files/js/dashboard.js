// dashboard.js

let salesChart, productsChart, userGrowthChart;

/**
 * Render Sales/Purchases chart
 */
function renderSales(data, role, canvasId) {
  const labels = data.map(item =>
    item.month
      ? new Date(item.month).toLocaleDateString("en-US", { month: "short", year: "numeric" })
      : "N/A"
  );
  const totals = data.map(item => item.total);

  if (salesChart) salesChart.destroy();
  salesChart = new Chart(document.getElementById(canvasId), {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: role === "Customer" ? "Your Purchases" : role === "Vendor" ? "Your Sales" : "Sales",
          data: totals,
          borderColor:
            role === "Vendor"
              ? "purple"
              : role === "Customer"
              ? "green"
              : "blue",
          backgroundColor:
            role === "Vendor"
              ? "rgba(155,89,182,0.2)"
              : role === "Customer"
              ? "rgba(46,204,113,0.2)"
              : "rgba(0,123,255,0.1)",
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: true, position: "bottom" } },
    },
  });
}

/**
 * Render Top Products chart
 */
function renderProducts(data) {
  const names = data.map(item => item.item__title);
  const totals = data.map(item => item.total_sold);

  if (productsChart) productsChart.destroy();
  productsChart = new Chart(document.getElementById("productsChart"), {
    type: "bar",
    data: {
      labels: names,
      datasets: [
        {
          label: "Units Sold",
          data: totals,
          backgroundColor: "rgba(255, 165, 0, 0.7)",
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
    },
  });
}

/**
 * Render User Growth chart
 */
function renderUserGrowth(data) {
  const labels = data.map(item =>
    item.month
      ? new Date(item.month).toLocaleDateString("en-US", { month: "short", year: "numeric" })
      : "N/A"
  );
  const totals = data.map(item => item.count);

  if (userGrowthChart) userGrowthChart.destroy();
  userGrowthChart = new Chart(document.getElementById("userGrowthChart"), {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "User Growth",
          data: totals,
          borderColor: "red",
          backgroundColor: "rgba(231,76,60,0.2)",
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: true, position: "bottom" } },
    },
  });
}

/**
 * Apply Filters (Admin Only)
 */
function applyFilters() {
  const start = document.getElementById("start_date")?.value || "";
  const end = document.getElementById("end_date")?.value || "";
  const cat = document.getElementById("category")?.value || "";

  const url = `/dashboard/sales-data/?start_date=${start}&end_date=${end}&category=${cat}`;
  fetch(url)
    .then(res => res.json())
    .then(data => renderSales(data, "Admin", "salesChart"));
}

/**
 * Init dashboard charts
 */
function initDashboard() {
  const role = document.body.dataset.role; // safer: set role in <body data-role="Admin">

  // Sales/Purchases Chart
  if (role === "Admin" && document.getElementById("salesChart")) {
    fetch("/dashboard/sales-data/")
      .then(res => res.json())
      .then(data => renderSales(data, "Admin", "salesChart"));
  } else if (role === "Vendor" && document.getElementById("vendorSalesChart")) {
    fetch("/dashboard/sales-data/")
      .then(res => res.json())
      .then(data => renderSales(data, "Vendor", "vendorSalesChart"));
  } else if (role === "Customer" && document.getElementById("customerOrdersChart")) {
    fetch("/dashboard/sales-data/")
      .then(res => res.json())
      .then(data => renderSales(data, "Customer", "customerOrdersChart"));
  }

  // Top Products (Admin & Vendor)
  if (document.getElementById("productsChart")) {
    fetch("/dashboard/top-products/")
      .then(res => res.json())
      .then(renderProducts);
  }

  // User Growth (Admin)
  if (document.getElementById("userGrowthChart")) {
    fetch("/dashboard/user-growth/")
      .then(res => res.json())
      .then(renderUserGrowth);
  }
}

// Auto-init
document.addEventListener("DOMContentLoaded", () => {
  initDashboard();
  setInterval(initDashboard, 15000); // auto-refresh every 15s
});

// Expose for Admin filter button
window.applyFilters = applyFilters;



function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = cookie.substring(name.length + 1);
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener("DOMContentLoaded", function() {
    const buttons = document.querySelectorAll(".vendor-action");
    const csrfToken = getCookie("csrftoken");

    buttons.forEach(btn => {
        btn.addEventListener("click", function() {
            const vendorId = this.dataset.vendorId;
            const action = this.dataset.action;

            fetch("", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: `vendor_id=${vendorId}&action=${action}`
            })
            .then(response => response.json())
            .then(data => {

                if (data.success) {
                    const row = document.getElementById(`vendor-row-${vendorId}`);
                    if (row) row.remove();

                    if(action === "approve"){
                        const approvedTable = document.getElementById("approved-vendors-body");
                        if(approvedTable){
                            const newRow = document.createElement("tr");
                            newRow.id = `vendor-row-${vendorId}`;
                            newRow.innerHTML = `
                                <td>New</td>
                                <td>${row.children[1].innerText}</td>
                                <td>${row.children[2].innerText}</td>
                                <td>${row.children[3].innerText}</td>
                                <td><span class="badge bg-success">Approved</span></td>
                            `;
                            approvedTable.appendChild(newRow);
                        }
                    }

                    const alertBox = document.createElement("div");
                    alertBox.className = `alert alert-${action == 'approve' ? 'success' : 'danger'} alert-dismissible fade show`;
                    alertBox.role = "alert";
                    alertBox.innerHTML = `
                        ${data.message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    `;

                    document.querySelector(".container-fluid").prepend(alertBox);
                } 
                else {
                    alert(data.message);
                }
            })
            .catch(err => console.error(err));
        });
    });
});

