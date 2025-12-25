// Image preview & ML placeholder
const imageInput = document.getElementById("imageInput");

if (imageInput) {
    imageInput.addEventListener("change", () => {
        const file = imageInput.files[0];
        if (file) {
            const mlFeedback = document.getElementById("ml-feedback");
            mlFeedback.classList.remove("hidden");
            mlFeedback.innerText = "Analyzing image with AI...";
        }
    });
}

//Vote Button for Backend
document.querySelectorAll(".vote-btn").forEach(button => {
    button.addEventListener("click", () => {
        const problemId = button.dataset.id;

        fetch(`/vote/${problemId}`, {
            method: "POST"
        })
        .then(async res => {
            const data = await res.json();

            // ❌ Handle error responses
            if (!res.ok) {
                alert(data.error || "Voting failed");
                return;
            }

            // ✅ Success case
            button.querySelector("span").innerText =
                data.votes + " Votes";

            button.classList.add("voted");
            button.disabled = true;
        })
        .catch(err => {
            console.error(err);
            alert("Something went wrong. Try again.");
        });
    });
});


