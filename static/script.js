window.onload = function () {
    if (document.getElementById("delete_account")) {
        document.getElementById("delete_account").addEventListener("click", function () {
            document.getElementById("f_delete_account").style.display = "block";
            document.getElementById("delete_account").style.display = "none";
        });
    }
    if (document.getElementsByClassName("alert-primary")) {
        let messages = document.getElementsByClassName("alert-primary");
        for (let i = 0; i < messages.length; i++) {
            messages[i].addEventListener("click", function () {
                this.remove();
            });
        }
    }
    if (document.getElementsByClassName("fa fa-star")) {
        let stars_empty = document.getElementsByClassName("fa fa-star");
        for (let i = 0; i < stars_empty.length; i++) {
            if (! stars_empty[i].classList.contains("checked")) {
                stars_empty[i].addEventListener("click", function () {
                    let recipe = JSON.parse(this.dataset.recipe);
                    fetch("/recipe/save", {
                        method: "POST",
                        body: JSON.stringify(recipe),
                        headers: {
                            "Content-Type": "application/json"
                        }
                    })
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === "success") {
                                this.classList.add("checked");
                            } else {
                                console.error(data.message);
                            }
                        })
                        .catch(error => console.error(error));
                });
            }
        }
    }
    if (document.getElementsByClassName("fa fa-star checked")) {
        let stars_full = document.getElementsByClassName("fa fa-star checked");
        for (let i = 0; i < stars_full.length; i++) {
            stars_full[i].addEventListener("click", function () {
                let recipe = JSON.parse(this.dataset.recipe);
                fetch("/recipe/remove", {
                    method: "POST",
                    body: JSON.stringify(recipe),
                    headers: {
                        "Content-Type": "application/json"
                    }
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === "success") {
                            this.classList.remove("checked");
                        } else {
                            console.error(data.message);
                        }
                    })
                    .catch(error => console.error(error));
            });
        }
    }
    // Get the form element
    let pagingForm = document.getElementById("paging_form");
    // Add an event listener to the form to listen for a submit event
    pagingForm.addEventListener("submit", function (event) {
        // Prevent the default form submission
        event.preventDefault();
        // Get the selected page number
        fetch("/update_paging_number", {
            method: "POST",
            body: new FormData(pagingForm)
        })
            .then(() => {
                location.reload();
            })
            .catch(error => console.error(error))
    });
}