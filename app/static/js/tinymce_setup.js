// TinyMCE编辑器

var globalcounter = 1;
tinymce.init({
    //选择class为content的标签作为编辑器
    selector: '#content',
    //方向从左到右
    directionality:'ltr',
    //语言选择中文
    language:'zh_CN',
    //高度为400
    height:400,
    //工具栏上面的补丁按钮
    plugins: [
            'advlist autolink link image lists charmap print preview hr anchor pagebreak spellchecker',
            'searchreplace wordcount visualblocks visualchars code fullscreen insertdatetime media nonbreaking',
            'save table contextmenu directionality emoticons template paste textcolor',
            'codesample',
        'code paste',//改
    ],
    //工具栏的补丁按钮
     toolbar: 'insertfile undo redo | \
     styleselect | \
     bold italic | \
     alignleft aligncenter alignright alignjustify | \
     bullist numlist outdent indent | \
     link image | \
     print preview media fullpage | \
     forecolor backcolor emoticons |\
     codesample fontsizeselect fullscreen',
    //字体大小
    fontsize_formats: '10pt 12pt 14pt 18pt 24pt 36pt',
    //按tab不换行
    nonbreaking_force_tab: true,
    paste_data_images: true,//改
    paste_preprocess: function(plugin, args) {
            args.content = args.content.replace("<img", "<img id=\"pasted_image_" + parseInt(globalcounter) + "\"");
            var xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function(){
                if (this.readyState == 4 && this.status == 200){
                    upload(this.response);
                }
            };
            // alert(args.content.split('"')[3]);
            if(args.content.split('"')[3] != undefined) {
                console.log(args.content);
                xhr.open('GET', args.content.split('"')[3]);//一粘贴，就开始请求这个本地图片地址，因为图片在本地，所以一定能请求成功，返回图片对象。然后上传。
                xhr.responseType = 'blob'; //0
                xhr.send();
            }
            function upload(BlobFile){
                var x = new XMLHttpRequest();
                x.onreadystatechange = function(){
                    if( this.readyState == 4 && this.status == 200 ){
                        data = this.responseText;
                        console.log('response data: ' + data);
                        id = parseInt(globalcounter++);
                        document.getElementById("content_ifr").contentWindow.document.getElementById("pasted_image_" + id).setAttribute("src", data);
                    }
                };
                x.open('POST', '/auth/pasteimg');
                x.send(BlobFile);
            }
        }
});