// ===============================
// Billing Software - JavaScript
// ===============================


// Show confirmation before logout
function confirmLogout() {

    return confirm(
        "Are you sure you want to logout?"
    );

}


// Mobile number validation
function validateMobile(mobile) {

    const pattern = /^[0-9]{10}$/;

    return pattern.test(mobile);

}


// Format amount
function formatAmount(amount) {

    amount = parseFloat(amount) || 0;

    return amount.toFixed(2);

}


// Calculate remaining amount
function calculateRemainingAmount(total, paid) {

    total = parseFloat(total) || 0;
    paid = parseFloat(paid) || 0;

    if (paid > total) {
        paid = total;
    }

    return total - paid;

}


// Confirm bill creation
function confirmBillCreation() {

    return confirm(
        "Do you want to create this bill?"
    );

}


// Auto-hide alert messages
document.addEventListener(
    "DOMContentLoaded",
    function () {

        const alerts =
            document.querySelectorAll(".alert");

        alerts.forEach(
            function (alert) {

                setTimeout(
                    function () {

                        alert.style.transition =
                            "opacity 0.5s";

                        alert.style.opacity = "0";

                        setTimeout(
                            function () {

                                alert.remove();

                            },
                            500
                        );

                    },
                    5000
                );

            }
        );

    }
);