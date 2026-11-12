const card = document.getElementById("owner-loyalty-card");

if (card) {
    const ownerId = card.dataset.ownerId;
    const rewardCost = Number(card.dataset.rewardCost);
    const balance = document.getElementById("loyalty-balance");
    const redeemButton = document.getElementById("loyalty-redeem");
    const status = document.getElementById("loyalty-status");
    const voucherList = document.getElementById("loyalty-vouchers");
    const emptyVouchers = document.getElementById("loyalty-vouchers-empty");
    let submitting = false;

    function setStatus(message, style) {
        status.textContent = message;
        status.classList.remove("alert-success", "alert-danger");
        status.classList.add(style === "success" ? "alert-success" : "alert-danger");
        status.hidden = !message;
    }

    function updateButton() {
        redeemButton.disabled = submitting || Number(balance.textContent) < rewardCost;
    }

    function renderVouchers(vouchers) {
        voucherList.replaceChildren();
        emptyVouchers.hidden = vouchers.length > 0;
        const formatter = new Intl.DateTimeFormat(card.dataset.locale, {dateStyle: "medium"});
        for (const voucher of vouchers) {
            const item = document.createElement("li");
            item.className = "list-group-item px-0 d-flex justify-content-between gap-3";

            const reference = document.createElement("span");
            reference.dataset.voucherReference = "";
            reference.textContent = voucher.reference;

            const time = document.createElement("time");
            time.dataset.voucherDate = "";
            time.dateTime = voucher.createdAt;
            const timestamp = new Date(voucher.createdAt);
            time.textContent = Number.isNaN(timestamp.getTime())
                ? String(voucher.createdAt).slice(0, 10)
                : formatter.format(timestamp);

            item.append(reference, time);
            voucherList.append(item);
        }
    }

    async function refresh() {
        const response = await fetch(`/owners/${encodeURIComponent(ownerId)}/loyalty`, {
            headers: {Accept: "application/json"}
        });
        if (!response.ok) throw new Error(card.dataset.errorLabel);
        const summary = await response.json();
        balance.textContent = summary.points;
        renderVouchers(summary.recentVouchers || []);
        updateButton();
    }

    redeemButton.addEventListener("click", async () => {
        if (submitting || Number(balance.textContent) < rewardCost) return;
        submitting = true;
        updateButton();
        setStatus("", "error");
        try {
            const response = await fetch(`/owners/${encodeURIComponent(ownerId)}/loyalty/redemptions`, {
                method: "POST",
                headers: {Accept: "application/json"}
            });
            if (response.status === 404) {
                setStatus(card.dataset.ownerNotFoundLabel, "error");
                return;
            }
            if (response.status === 409) {
                setStatus(card.dataset.insufficientLabel, "error");
                await refresh();
                return;
            }
            if (response.status !== 201) {
                throw new Error(card.dataset.errorLabel);
            }
            const redemption = await response.json();
            balance.textContent = redemption.points;
            setStatus(card.dataset.successLabel, "success");
            // Redemption has committed. A refresh failure must not suggest it failed.
            try {
                await refresh();
            } catch {
                // Keep the confirmed balance and success message until the page is reloaded.
            }
        } catch {
            setStatus(card.dataset.errorLabel, "error");
        } finally {
            submitting = false;
            updateButton();
        }
    });

    updateButton();
}
