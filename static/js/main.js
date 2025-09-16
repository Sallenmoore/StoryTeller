// 📁 main.js
import * as utility from "./utility.js";
window.strip_html = utility.strip_html;
//htmx.logAll();
//===My document.ready() handler...
document.body.addEventListener('htmx:configRequest', utility.process_form_values);
htmx.onLoad(function (e) {
    //////////////////////   Show/Hide Back to Top Button  //////////////////////
    window.addEventListener('scroll', function () {
        var backToTopButton = document.getElementById("back-to-top");
        if (window.scrollY > 300) {
            backToTopButton.style.display = "block";
        } else {
            backToTopButton.style.display = "none";
        }
    });
});

