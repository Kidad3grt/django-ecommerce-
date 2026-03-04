// ----------------------
// VENDOR DASHBOARD SCRIPT
// ----------------------

// Get CSRF token from cookie
function getCSRFToken() {
    let cookieValue = null;
    const cookies = document.cookie.split(';');

    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith("csrftoken=")) {
            cookieValue = cookie.substring("csrftoken=".length, cookie.length);
            break;
        }
    }
    return cookieValue;
}

const csrftoken = getCSRFToken();

// ----------------------
// DELETE PRODUCT
// ----------------------
document.querySelectorAll(".delete-product").forEach(btn => {
    btn.addEventListener("click", function () {
        const productId = this.dataset.id;

        if (!confirm("Are you sure you want to delete this product?")) {
            return;
        }

        fetch(`/vendor/product/delete/${productId}/`, {
            method: "DELETE",
            headers: {
                "X-CSRFToken": csrftoken,
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert("Error: " + data.error);
            } else {
                // Remove row from table instantly
                document.getElementById(`product-${productId}`).remove();
                alert("Product deleted successfully");
            }
        })
        .catch(error => console.error("Error:", error));
    });
});


// ----------------------
// UPDATE ORDER STATUS
// ----------------------
document.querySelectorAll(".update-status").forEach(select => {
    select.addEventListener("change", function () {
        const orderId = this.dataset.id;
        const newStatus = this.value;

        fetch(`/vendor/order/status/${orderId}/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrftoken,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ status: newStatus })
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert("Error updating status: " + data.error);
            } else {
                alert("Order status updated to " + newStatus);
            }
        })
        .catch(error => console.error("Error:", error));
    });
});
