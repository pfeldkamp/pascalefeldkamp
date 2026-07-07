document.querySelectorAll(".copy-btn").forEach(button => {
    button.addEventListener("click", async () => {
        await navigator.clipboard.writeText(button.dataset.copy);

        button.classList.add("copied");

        setTimeout(() => {
            button.classList.remove("copied");
        }, 1500);
    });
});