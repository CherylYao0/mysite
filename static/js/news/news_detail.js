$(function () {
    // 对评论进行评论
    $('.comment-list').delegate('a,input', 'click', function () {
        //获取回复按钮的class属性
        let sClassValue = $(this).prop('class');
        // 如果点击的是回复按钮，就显示输入框
        if (sClassValue.indexOf('reply_a_tag') >= 0) {
            $(this).next().toggle();
        }
        // 如果点击的是取消按钮，就隐藏输入框
        if (sClassValue.indexOf('reply_cancel') >= 0) {
            $(this).parent().toggle();
        }

        if (sClassValue.indexOf('reply_btn') >= 0) {
            // 评论
            let $this = $(this);
            let news_id = $this.parent().attr('news-id');
            let parent_id = $this.parent().attr('comment-id');
            let content = $this.prev().val();
            if (!content) {
                message.showError('请输入评论内容！');
                return
            }
            $
                .ajax({
                    url: '/news/' + news_id + '/comment/',
                    type: 'POST',
                    data: {
                        content: content,
                        parent_id: parent_id
                    },
                    dataType: "json"
                })

                .done((res) => {
                    if (res.errno === '0') {
                        let comment = res.data;
                        let html_comment = `<li class="comment-item">
            <div class="comment-info clearfix">
              <img src="/static/images/avatar.jpeg" alt="avatar" class="comment-avatar">
              <span class="comment-user">${comment.author}</span>
              <span class="comment-pub-time">${comment.update_time}</span>
            </div>
            <div class="comment-content">${comment.content}</div>
                <div class="parent_comment_text">
                  <div class="parent_username">${comment.parent.author}</div>
                  <div class="comment_time">${comment.parent.update_time}</div>
                  <div class="parent_content_text">
                    ${comment.parent.content}
                  </div>
                </div>
              // <div class="comment_time left_float">${comment.update_time}</div>
              <a href="javascript:;" class="reply_a_tag right_float">回复</a>
              <form class="reply_form left_float" comment-id="${comment.content_id}" news-id="${comment.news_id}">
                <textarea class="reply_input"></textarea>
                <input type="button" value="回复" class="reply_btn right_float">
                <input type="reset" name="" value="取消" class="reply_cancel right_float">
              </form>
          </li>`;
                        message.showSuccess('评论成功！');
                        setTimeout(() => {
                            $('.comment-list').prepend(html_comment);
                        }, 800);

                        $this.prev().val('');   // 清空输入框
                        $this.parent().hide();  // 关闭评论框
                    } else if (res.errno === '4101') {
                        // 用户未登录
                        message.showError(res.errmsg);
                        setTimeout(() => {
                            window.location.href = '/users/login/'
                        }, 800)
                    } else {
                        // 失败
                        message.showError(res.errmsg)
                    }
                })
                .fail(() => {
                    message.showError('服务器超时，请重试')
                })
        }
    });
    // 对新闻评论
    let $newsComment = $('.logged-comment input');            // 新闻评论框
    let $sendComment = $('.comment-pub .comment-btn');           // 新闻评论按钮

    $sendComment.click(function () {

        let $this = $(this);
        if ($this.prev().hasClass('please-login-comment')) {
            message.showError('未登录，请登录后再评论！');
            setTimeout(() => {
                window.location.href = '/users/login/'
            }, 800);
            return
        }
        let news_id = $this.prev().attr('news-id');
        let content = $newsComment.val();
        if (!content) {
            message.showError('请输入评论内容！');
            return
        }
        $
            .ajax({
                url: '/news/' + news_id + '/comment/',
                type: 'POST',
                data: {
                    content: content
                },
                dataType: 'json'
            })
            .done((res) => {
                if (res.errno === '0') {
                    let comment = res.data;
                    console.log(comment)
                    let html_comment = `<li class="comment-item">
            <div class="comment-info clearfix">
              <img src="/static/images/avatar.jpeg" alt="avatar" class="comment-avatar">
              <span class="comment-user">${comment.author}</span>
              <span class="comment-pub-time">${ comment.update_time }</span>
            </div>
            <div class="comment-content">${comment.content}</div>
              <a href="javascript:;" class="reply_a_tag right_float">回复</a>
              <form class="reply_form left_float" comment-id="${comment.content_id}" news-id="${comment.news_id}">
                <textarea class="reply_input"></textarea>
                <input type="button" value="回复" class="reply_btn right_float">
                <input type="reset" name="" value="取消" class="reply_cancel right_float">
              </form>
          </li>`;
                    message.showSuccess('评论成功！');
                    setTimeout(() => {
                        $(".comment-list").prepend(html_comment);
                    }, 800);
                    // 清空
                    $newsComment.val('');
                } else if (res.errno === '4101') {
                    // 用户未登录
                    message.showError(res.errmsg);
                    setTimeout(() => {
                        window.location.href = '/users/login/'
                    }, 800)
                } else {
                    message.showError(res.errmsg);
                }
            })
            .fail(() => {
                message.showError('服务器超时，请重试！');
            })
    })
});