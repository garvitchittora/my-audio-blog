let canonicalURL;

if(window.location.hostname.startsWith("myaudioblogs")){
    canonicalURL = "https://www."+window.location.hostname+window.location.pathname;
}else{
    canonicalURL = "https://"+window.location.hostname+window.location.pathname;
}

$("head").append(`<link rel="canonical" href="${canonicalURL}" />`);

$(document).ready(function () {
    $('.faq-block .block-header').on('click', function () {
        $(this).toggleClass('is-active');
        $(this).closest('.faq-block').find('.block-body').slideToggle('fast');
    });
});