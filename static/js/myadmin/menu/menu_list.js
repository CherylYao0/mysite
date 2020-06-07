$(() => {
    let $deleteBtns = $('button.delete');       // 删除按钮
    menuId = 0;                                 // 这里不要用let 被点击菜单id 要设置为全局变量
    let $currentMenu = null;                    // 当前被点击菜单对象

    $deleteBtns.click(function () {
        let $this = $(this);
        $currentMenu = $this.parent().parent();   // 获取的是点击的删除按钮所在的tr标签
        menuId = $this.parent().data('id');
        let menuName = $this.parent().data('name');

        // 改变模态框的显示内容
        $('#modal-delete .modal-body p').html('确定删除菜单:《' + menuName + '》?');
        // 显示 模态框
        $('#modal-delete').modal('show');

    });

    $('#modal-delete button.delete-confirm').click(() => {
        deleteMenu()
    });

    // 删除菜单的函数
    function deleteMenu() {
        $
            .ajax({
                url: '/admin/menu/' + menuId + '/',
                type: 'DELETE',
                dataType: 'json'
            })
            .done((res) => {
                if (res.errno === '0') {
                    // 关闭模态框
                    $('#modal-delete').modal('hide');
                    // 删除菜单元素
                    $currentMenu.remove();
                    message.showSuccess('删除成功！');
                } else {
                    message.showError(res.errmsg)
                }
            })
            .fail(() => {
                message.showError('服务器超时请重试！')
            })
    }


    // 编辑菜单
    let $editBtns = $('button.edit');           // 编辑按钮
    $editBtns.click(function () {
        let $this = $(this);
        $currentMenu = $this.parent().parent();
        menuId = $this.parent().data('id');

        $
            .ajax({
                url: '/admin/menu/' + menuId + '/',
                type: 'GET'
            })
            .done((res)=>{
                // 改变模态框的内容
                $('#modal-update .modal-content').html(res);
                // 显示模态框
                $('#modal-update').modal('show')
            })
            .fail(()=>{
                message.showError('服务器超时，请重试！')
            })
    })
});