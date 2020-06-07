$(() => {
    let $addBtn = $('button.add');          //  模态框中的添加按钮
    let $form = $('#add-menu');             //  模态矿中的表单

    $addBtn.click(function () {

        $
            .ajax({
                url: '/admin/menu/',
                type: 'POST',
                data: $form.serialize(),
            })
            .done((res) => {
                if (res.errno === '0') {
                    // 添加成功，关闭模态框，并刷新菜单列表
                    $('#modal-add').modal('hide').on('hidden.bs.modal', function (e) {
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
                    message.showError('添加菜单失败！');
                    // 更新模特框中的表单信息
                    $('#modal-add .modal-content').html(res)
                }
            })
            .fail(() => {
                message.showError('服务器超时，请重试');
            });
    });

});