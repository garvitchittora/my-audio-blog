$(document).ready(function () {
    let clap = $(".clap-blog");
    let bookmark = $(".bookmark");
    let followButton = $(".follow-button");
    let radioVisibity = $("input[name=visibility]")
    let audioButton = $(".editing-info .audio-button")
    let hostname = "https://"+window.location.hostname;
    if(hostname == "https://localhost"){
        hostname = "http://localhost:8000";
    }

    clap.click(function () {
        let blog_id = $(this).attr("data-blog-id");
        
        fetch(`${hostname}/addClap/`, {
            method: "POST",

            body: JSON.stringify({
                id: blog_id,
            }),

            headers: {
                "Content-type": "application/json; charset=UTF-8",
                "X-CSRFToken": csrftoken
            },
        }).then((response) => response.json())
            .then((output) => {
                let count = output['data']['viewer_clap_count'];
                $(".clap-count").html(output['data']['clap_count']);
                if (count == 1) {
                    $(this).html(`<svg width="29" height="29" aria-label="clap">
                <g fill-rule="evenodd">
                  <path
                    d="M13.74 1l.76 2.97.76-2.97zM18.63 2.22l-1.43-.47-.4 3.03zM11.79 1.75l-1.43.47 1.84 2.56zM24.47 14.3L21.45 9c-.29-.43-.69-.7-1.12-.78a1.16 1.16 0 0 0-.91.22c-.3.23-.48.52-.54.84l.05.07 2.85 5c1.95 3.56 1.32 6.97-1.85 10.14a8.46 8.46 0 0 1-.55.5 5.75 5.75 0 0 0 3.36-1.76c3.26-3.27 3.04-6.75 1.73-8.91M14.58 10.89c-.16-.83.1-1.57.7-2.15l-2.5-2.49c-.5-.5-1.38-.5-1.88 0-.18.18-.27.4-.33.63l4.01 4z">
                  </path>
                  <path
                    d="M17.81 10.04a1.37 1.37 0 0 0-.88-.6.81.81 0 0 0-.64.15c-.18.13-.71.55-.24 1.56l1.43 3.03a.54.54 0 1 1-.87.61L9.2 7.38a.99.99 0 1 0-1.4 1.4l4.4 4.4a.54.54 0 1 1-.76.76l-4.4-4.4L5.8 8.3a.99.99 0 0 0-1.4 0 .98.98 0 0 0 0 1.39l1.25 1.24 4.4 4.4a.54.54 0 0 1 0 .76.54.54 0 0 1-.76 0l-4.4-4.4a1 1 0 0 0-1.4 0 .98.98 0 0 0 0 1.4l1.86 1.85 2.76 2.77a.54.54 0 0 1-.76.76L4.58 15.7a.98.98 0 0 0-1.4 0 .99.99 0 0 0 0 1.4l5.33 5.32c3.37 3.37 6.64 4.98 10.49 1.12 2.74-2.74 3.27-5.54 1.62-8.56l-2.8-4.94z">
                  </path>
                </g>
              </svg>`);
                }
                if(count != 0){
                    $(this).prepend(`<div class="clap-count-user">+ ${count}</div>`).find('.clap-count-user').fadeOut(1000);
                }
            })
    });

    bookmark.click(function () {
        let marked = $(this).attr("data-marked");
        let blog_id = $(this).attr("data-blog-id");
        
        if (marked == 0) {
            for(i=0;i<bookmark.length;i++){
                if($(bookmark[i]).attr("data-blog-id") == $(this).attr("data-blog-id") ){
                    $(bookmark[i]).html(`<svg width="25" height="25" viewBox="0 0 25 25">
                            <path
                            d="M19 6a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v14.66h.01c.01.1.05.2.12.28a.5.5 0 0 0 .7.03l5.67-4.12 5.66 4.13c.2.18.52.17.71-.03a.5.5 0 0 0 .12-.29H19V6z">
                            </path>
                        </svg>`);
                }
            }
            
          $(this).attr("data-marked", "1");

            fetch(`${hostname}/bookMarkBlog/`, {
                method: "POST",

                body: JSON.stringify({
                    id: blog_id,
                    bookMarkFlag: 1,
                }),

                headers: {
                    "Content-type": "application/json; charset=UTF-8",
                    "X-CSRFToken": csrftoken
                },
            })
            // .then((response) => {
            //     console.log(response);
            // })
        } else {
            for(i=0;i<bookmark.length;i++){
                if($(bookmark[i]).attr("data-blog-id") == $(this).attr("data-blog-id") ){
                    $(bookmark[i]).html(`<svg width="25" height="25" viewBox="0 0 25 25">
                    <path
                      d="M19 6a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v14.66h.01c.01.1.05.2.12.28a.5.5 0 0 0 .7.03l5.67-4.12 5.66 4.13a.5.5 0 0 0 .71-.03.5.5 0 0 0 .12-.29H19V6zm-6.84 9.97L7 19.64V6a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v13.64l-5.16-3.67a.49.49 0 0 0-.68 0z"
                      fill-rule="evenodd"></path>
                  </svg>`);
                }
            }
          $(this).attr("data-marked", "0");

            fetch(`${hostname}/bookMarkBlog/`, {
                method: "POST",

                body: JSON.stringify({
                    id: blog_id,
                    bookMarkFlag: 0,
                }),

                headers: {
                    "Content-type": "application/json; charset=UTF-8",
                    "X-CSRFToken": csrftoken
                },
            })
            // .then((response) => {
            //     console.log(response);
            // })
        }
    });

    followButton.click(function () {
        let user_id = $(this).attr("data-user-id");
        fetch(`${hostname}/followUser/`, {
            method: "POST",

            body: JSON.stringify({
                user_id: user_id,
            }),

            headers: {
                "Content-type": "application/json; charset=UTF-8",
                "X-CSRFToken": csrftoken
            },
        }).then((response) => response.json())
            .then((output) => {
                if(output.data.followed){
                    for(i=0;i<followButton.length;i++){
                        if($(followButton[i]).attr("data-user-id") == user_id){
                            $(followButton[i]).html('Unfollow');
                            $(followButton[i]).removeClass('btn-success');
                            $(followButton[i]).addClass('btn-light');
                        }
                    }
                }else{
                    for(i=0;i<followButton.length;i++){
                        if($(followButton[i]).attr("data-user-id") == user_id){
                            $(followButton[i]).html('Follow');
                            $(followButton[i]).addClass('btn-success');
                            $(followButton[i]).removeClass('btn-light');
                        }
                    }
                }
            })
    });

    $(".modalOpenButton").on('click', function () {
        let modal = $(this).next(".modal");
        modal.css("display", "block");
        $(modal).find(".close").on('click', function () {
            modal.css("display", "none");
        });
    });

    $(radioVisibity).change(function () {
        if (this.value == 'public') {
            fetch(`${hostname}/changeVisibilty/`, {
                method: "POST",

                body: JSON.stringify({
                    id: blog_id,
                    is_private:false
                }),

                headers: {
                    "Content-type": "application/json; charset=UTF-8",
                    "X-CSRFToken": csrftoken
                },
            }).then((response) => {
                let notificationDiv = $(".notification-container .notification-v");
                if(response.status ==200){
                    notificationDiv.css("display","block").css("background","#5cb85c").html("Visibility changed to Public").fadeOut(5000);
                }else{
                    notificationDiv.css("display","block").css("background","#d9534f").html("Error Occured").fadeOut(5000);
                }
            });
        }
        else if (this.value == 'private') {
            fetch(`${hostname}/changeVisibilty/`, {
                method: "POST",

                body: JSON.stringify({
                    id: blog_id,
                    is_private:true
                }),

                headers: {
                    "Content-type": "application/json; charset=UTF-8",
                    "X-CSRFToken": csrftoken
                },
            }).then((response) => {
                let notificationDiv = $(".notification-container .notification-v");
                if(response.status ==200){
                    notificationDiv.css("display","block").css("background","orange").html("Visibility changed to Private").fadeOut(5000);
                }else{
                    notificationDiv.css("display","block").css("background","#d9534f").html("Error Occured").fadeOut(5000);
                }
            })
        }
    });

    async function get_audio(blog_id){
        let status;
        let response = await fetch(`${hostname}/getAudio?id=${blog_id}`, {
            method: "GET",

            headers: {
                "Content-type": "application/json; charset=UTF-8",
                "X-CSRFToken": csrftoken
            },
        }).then((response) => {
            status = response.status;
            return response;
        });

        return status;
    }

    audioButton.click(async function () {
        fetch(`${hostname}/createAudio/`, {
            method: "POST",

            body: JSON.stringify({
                id: blog_id,
            }),

            headers: {
                "Content-type": "application/json; charset=UTF-8",
                "X-CSRFToken": csrftoken
            },
        }).then(async (response) => {
            if(response.status==200){
                let setIntervalVar;
                let count = 0;
                $("#audio-genration-content div").html("<p>Processing...</p>");

                setIntervalVar = setInterval(function () {
                    get_audio(blog_id).then(status => {
                        if(status==200){
                            clearInterval(setIntervalVar);
                            $("#audio-genration-content div").html("<p>Created successfully! <br>To listen audio, Please the refresh page.</p>");
                        }else{
                            count = count + 1;
                            if(count>=60){
                                clearInterval(setIntervalVar);
                                $("#audio-genration-content div").html("<p>Error occured</p>");
                            }
                        }
                    });
                }, 5000);
            }
        })
    });

});

function copyLink(){
    let dummy = document.createElement('input'),
    text = window.location.href;
    document.body.appendChild(dummy);
    dummy.value = text;
    dummy.select();
    document.execCommand('copy');
    document.body.removeChild(dummy);
    let notificationDiv = $(".notification-container .notification-v");
    notificationDiv.css("display","block").css("background","green").html("copied!").fadeOut(5000);
}