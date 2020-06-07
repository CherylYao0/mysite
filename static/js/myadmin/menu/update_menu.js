$(()=>{
    let $updateBtn = $('#modal-update button.update');
    let $form = $('#update-menu');
    $updateBtn.click(function () {
        $
            .ajax({
                url: '/admin/menu/' + menuId + '/',
                type: 'PUT',
                data: $form.serialize(),
            })
            .done((res) => {
                if (res.errno === '0') {
                    $('#modal-update').modal('hide').on('hidden.bs.modal', function (e) {
                        $('#content').load(
                            $('.sidebar-menu li.active a').data('url'),
                            (response, status, xhr) => {
                                if (status !== 'success') {
                                    message.showError('服务器超时，请重试！')
                                }
                            }
                        );
                    });
                    message.showSuccess(res.errmsg);
                } else {
                    message.showError('修改菜单失败！');
                    // 修改模态框内容为，返回的渲染了错误信息的表单
                    $('#modal-update .modal-content').html(res)
                }
            })
            .fail(() => {
                message.showError('服务器超时，请重试');
            });
    });
});