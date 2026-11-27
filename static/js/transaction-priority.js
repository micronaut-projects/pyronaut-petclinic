// Each fetch stays open until its own database transaction commits or rolls back.
const root = document.getElementById("transaction-priority-page");
if (root) {
    const element = id => root.querySelector("#priority-" + id);
    const labels = Object.fromEntries([...root.querySelectorAll("[data-key]")]
        .map(node => [node.dataset.key, node.textContent]));
    const text = key => labels[key] ?? key;
    const select = element("appointment-select");
    let appointmentId;
    let lowPending = false;
    let highPending = false;
    let resetPending = false;
    let lowOutcome = "NOT_STARTED";
    let highOutcome = "NOT_STARTED";
    let countdown;

    function render() {
        element("start-low").disabled = resetPending || lowPending || highPending || !select.value;
        element("start-high").disabled = resetPending || highPending || !select.value
            || (lowPending && highOutcome !== "NOT_STARTED");
        element("reset").disabled = resetPending || lowPending || highPending;
        select.disabled = resetPending || lowPending || highPending;
        element("low").textContent = text("outcome." + lowOutcome);
        element("high").textContent = text("outcome." + highOutcome);

        let summary = "working";
        if (lowOutcome === "FAILED" || highOutcome === "FAILED") summary = "error";
        else if (lowOutcome === "PRIORITY_ROLLED_BACK" && highOutcome === "COMMITTED") summary = "confirmed";
        else if (lowOutcome === "COMMITTED") summary = "regularWon";
        else if (lowOutcome === "TAKEN" || highOutcome === "TAKEN") summary = "taken";
        else if (lowOutcome === "TIMED_OUT" || highOutcome === "TIMED_OUT") summary = "timedOut";
        else if (highOutcome === "COMMITTED" && lowOutcome === "NOT_STARTED") summary = "emergencyWon";
        else if (highOutcome === "COMMITTED") summary = "emergencyPending";
        element("summary").textContent = text(summary);
    }

    function updateAppointments(appointments) {
        appointments ??= []; // Serialization can omit an empty availability list.
        if (!Array.isArray(appointments)) {
            select.replaceChildren(new Option(text("error"), ""));
            element("suggestion").textContent = "—";
            showError(new Error(text("error")));
            return;
        }
        const previous = select.value;
        const previousStillAvailable = appointments.some(a => String(a.id) === previous);
        select.replaceChildren();
        if (appointments.length) {
            select.add(new Option(text("ready"), ""));
            for (const appointment of appointments) {
                select.add(new Option(appointment.displayOrder + ". " + appointment.label, appointment.id));
            }
            // Selecting the next appointment does not book it; the user must start a new request.
            select.value = previousStillAvailable ? previous : String(appointments[0].id);
        } else {
            select.add(new Option(text("noAvailable"), ""));
        }
        element("suggestion").textContent = appointments[0]?.label ?? text("noAvailable");
    }

    function showError(error) {
        element("error").textContent = error.message;
        element("error").classList.remove("d-none");
    }

    async function request(path) {
        const response = await fetch("/oracle/transaction-priority" + path, {
            method: "POST", headers: {Accept: "application/json"}
        });
        const body = await response.json().catch(() => {
            throw new Error(text("error"));
        });
        if (!response.ok && !body.outcome) throw new Error(body.message || text("error"));
        return body;
    }

    async function book(kind) {
        const result = await request("/book?appointmentId=" + encodeURIComponent(appointmentId)
            + "&type=" + encodeURIComponent(kind));
        if (!result.outcome) throw new Error(text("error"));
        element("database-status").textContent = result.databaseStatus;
        updateAppointments(result.availableAppointments);
        return result.outcome;
    }

    element("start-low").addEventListener("click", async () => {
        if (resetPending || lowPending || highPending || !select.value) return;
        appointmentId = select.value; // Both requests use this ID, even when the options refresh.
        element("appointment").textContent = select.selectedOptions[0].textContent;
        element("state").classList.remove("d-none");
        element("error").classList.add("d-none");
        element("database-status").textContent = "—";
        element("suggestion").textContent = "—";
        lowPending = true;
        lowOutcome = "RUNNING";
        highOutcome = "NOT_STARTED";
        element("countdown-value").classList.remove("d-none");
        const deadline = Date.now() + Number(root.dataset.reservationSeconds) * 1000;
        const tick = () => {
            const seconds = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
            element("countdown").textContent = text(seconds ? "countdown" : "completing");
            element("countdown-value").textContent =
                String(Math.floor(seconds / 60)).padStart(2, "0") + ":" + String(seconds % 60).padStart(2, "0");
        };
        tick();
        countdown = setInterval(tick, 1000);
        render();
        try {
            lowOutcome = await book("regular");
        } catch (error) {
            lowOutcome = "FAILED";
            showError(error);
        } finally {
            lowPending = false;
            clearInterval(countdown);
            element("countdown").textContent = text("finished");
            element("countdown-value").classList.add("d-none");
            render();
        }
    });

    element("start-high").addEventListener("click", async () => {
        if (resetPending || highPending || !select.value || (lowPending && highOutcome !== "NOT_STARTED")) return;
        if (!lowPending) {
            appointmentId = select.value;
            element("appointment").textContent = select.selectedOptions[0].textContent;
            element("state").classList.remove("d-none");
            element("error").classList.add("d-none");
            element("database-status").textContent = "—";
            element("suggestion").textContent = "—";
            lowOutcome = "NOT_STARTED";
            element("countdown").textContent = "";
            element("countdown-value").classList.add("d-none");
        }
        highPending = true;
        highOutcome = "RUNNING";
        render();
        try {
            highOutcome = await book("emergency");
        } catch (error) {
            highOutcome = "FAILED";
            showError(error);
        } finally {
            highPending = false;
            render();
        }
    });

    element("reset").addEventListener("click", async () => {
        if (resetPending || lowPending || highPending) return;
        resetPending = true;
        render();
        try {
            await request("/reset");
            window.location.reload();
        } catch (error) {
            showError(error);
            resetPending = false;
            render();
        }
    });

    select.addEventListener("change", render);
    render();
    window.addEventListener("pagehide", () => clearInterval(countdown));
    window.addEventListener("pageshow", event => {
        if (event.persisted) window.location.reload();
    });
}
