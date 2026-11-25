(function () {
    "use strict";
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // Hora de Colombia, se actualiza sola
    var hora = document.getElementById("hora-hoy");
    if (hora) {
        var tick = function () {
            try {
                hora.textContent = new Date().toLocaleTimeString("es-CO", {
                    hour: "numeric", minute: "2-digit", hour12: true, timeZone: "America/Bogota"
                });
            } catch (e) {}
        };
        tick();
        setInterval(tick, 20000);
    }

    if (reduce) return;

    // Burbujas que suben desde el fondo
    var layer = document.querySelector(".bubbles");
    function bubble(x, big) {
        if (!layer) return;
        var b = document.createElement("span");
        var size = big ? 14 + Math.random() * 30 : 8 + Math.random() * 26;
        b.className = "bubble";
        b.style.width = b.style.height = size + "px";
        b.style.left = (x !== undefined ? x : Math.random() * 100) + (x !== undefined ? "px" : "%");
        b.style.setProperty("--dx", (Math.random() * 80 - 40) + "px");
        b.style.animationDuration = (big ? 3 + Math.random() * 3 : 9 + Math.random() * 9) + "s";
        layer.appendChild(b);
        setTimeout(function () { b.remove(); }, 20000);
    }
    var count = window.innerWidth < 700 ? 6 : 12;
    for (var i = 0; i < count; i++) setTimeout(bubble, i * 700);
    setInterval(bubble, 1800);

    // Al tocar la pantalla, aparece un aro que se expande como una gota
    document.addEventListener("pointerdown", function (e) {
        var p = document.createElement("span");
        p.className = "pop";
        p.style.left = e.clientX + "px";
        p.style.top = e.clientY + "px";
        document.body.appendChild(p);
        setTimeout(function () { p.remove(); }, 700);
    });

    // Al guardar un registro, una ráfaga de burbujas celebra
    if (document.querySelector(".alert.success")) {
        for (var j = 0; j < 26; j++) {
            (function (k) { setTimeout(function () { bubble(Math.random() * window.innerWidth, true); }, k * 60); })(j);
        }
    }
})();
