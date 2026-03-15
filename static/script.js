function showTab(id, btn) {
    document.querySelectorAll(".tab-content")
        .forEach(tab => tab.classList.remove("active"));

    document.querySelectorAll(".tab-btn")
        .forEach(button => button.classList.remove("active"));

    document.getElementById(id).classList.add("active");
    btn.classList.add("active");
}

// UPDATE 1: Now accepts vendor_name so the kitchen knows whose order it is
function addToCart(item, price, vendor_name) {
    fetch("/add_to_cart", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item: item, price: price, vendor_name: vendor_name })
    }).then(() => {
        showToast();
        loadCart();
    });
}

function loadCart() {
    fetch("/get_cart")
        .then(res => res.json())
        .then(data => {
            let html = "";
            let total = 0;
            data.forEach(d => {
                total += d[1] * d[2];
                html += `
                <div class="cart-item">
                    <span>${d[0]} <small style="color: #38bdf8;">(${d[3] || 'Vendor'})</small></span>
                    <div class="qty-controls">
                        <button onclick="updateQty('${d[0]}','decrease')">−</button>
                        <span>${d[2]}</span>
                        <button onclick="updateQty('${d[0]}','increase')">+</button>
                    </div>
                    <button onclick="removeItem('${d[0]}')">Remove</button>
                </div>
                `;
            });
            document.getElementById("cart-items").innerHTML = html;
            document.getElementById("cart-total").innerText = "Total: ₹" + total;
            document.getElementById("cart-count").innerText = data.length;
        });
}

function updateQty(item, action) {
    fetch("/update_quantity", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item, action })
    }).then(loadCart);
}

function removeItem(item) {
    fetch("/remove_item", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item })
    }).then(loadCart);
}

function openCart() {
    document.getElementById("cartDrawer").classList.add("open");
}

function closeCart() {
    document.getElementById("cartDrawer").classList.remove("open");
}

function openPayment() {
    document.getElementById("paymentModal").style.display = "flex";
}

// UPDATE 2: Now points to /checkout instead of /clear_cart
function placeOrder() {
    fetch("/checkout", { method: "POST" })
        .then(() => {
            alert("Order placed successfully! The kitchen is preparing your food.");
            document.getElementById("paymentModal").style.display = "none";
            closeCart();
            loadCart();
        });
}

function closePayment() {
    document.getElementById("paymentModal").style.display = "none";
}

function showToast() {
    const toast = document.getElementById("toast");
    toast.style.display = "block";
    setTimeout(() => toast.style.display = "none", 2000);
}