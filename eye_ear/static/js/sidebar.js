$(document).ready(function () {
    const sideLeftTop = $(".side-left-container")[0].offsetTop + $(".side-left-container")[0].offsetHeight;
    let is_mobile = false;
    if($(window).width()<=768){
        is_mobile = true;
    }

    document.body.onscroll = function (e) {
        if(! is_mobile){
            let footerTop = $("footer")[0].offsetTop - $(window).scrollTop() - 30;
            if (sideLeftTop > footerTop) {
                $(".side-left-container").css("display", "none");
            } else {
                $(".side-left-container").css("position", "fixed");
                $(".side-left-container").css("display", "block");
            }
        }
    }
});