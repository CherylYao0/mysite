$(function () {
    let $loginBtn = $('.login-btn');    // 获取登录按钮元素
    $loginBtn.click(function (e) {
        e.preventDefault(); // 阻止默认提交
        // 1.校验账户
        let sAccount = $('input[name="account"]').val();
        if (sAccount === ''){
            message.showError('用户账户不能为空');
            return
        }
        if(!(/^\w{5,20}$/).test(sAccount) && !(/^1[3-9]\d{9}$/).test(sAccount)){
            message.showError('用户账户格式不正确，请求重新输入');
            return
        }
        // 2.校验用户输入密码
        let sPassword = $('input[name="password"]').val();
        if(sPassword === ''){
            message.showError('用户密码不能为空');
            return
        }
        // 3.获取用户是否勾选'记住我'，勾选为true，否则为false
        let bRemember = $('input[name="remember"]').is(':checked');
        // 4.发送ajax
        $.ajax({
            url: '/users/login/',
            data: {
                account: sAccount,
                password: sPassword,
                remember: bRemember
            },
            type: 'POST',
            dataType: 'json',
            success: function (res) {
                if(res.errno === '0'){
                    message.showSuccess('恭喜， 登录成功！');
                    setTimeout(function () {
                        //注册成功之后重定向到打开登录页面之前的页面
                        if(!document.referrer || document.referrer.includes('/users/login/') || document.referrer.includes('/users/register/')){
                            window.location.href = '/'
                        }else {
                            window.location.href = document.referrer
                        }
                    }, 1000)
                }else{
                    message.showError(res.errmsg)
                }
            },
            error: function (xhr, msg) {
                message.showError('服务器超时，请重试')

            }
        });
    });
});