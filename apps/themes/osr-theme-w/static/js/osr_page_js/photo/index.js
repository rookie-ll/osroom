
    var vue = new Vue({
      el: '#app',
      delimiters:['{[', ']}'],
      data:{
            photos:[{}],
            photo_nav:[],
            current_category:[],
            sort:"t-desc",
            pages:[],
            page:1,
            colors:[],
            img_w_h:"?w=0&h=120",
      },
      filters: {
            formatDate: function (time) {
              return irrformatDate(time, "yyyy-MM-dd hh:mm");
            }
      },
      updated:function(){
        //每次渲染完执行
        this.$nextTick(function(){
            if(this.current_category.length < 2){
                    var index = this.photo_nav.indexOf(this.current_category[0]);

                    nav_btn_active("img-category", "head_li_"+index);
                }else{
                    nav_btn_active("img-category", "head_li_all");
            }
        });
      }
    })

    // 加载完页面执行
    $(document).ready(function(){

        vue.colors =  osr_colors();
        result = get_show_category();
        result.then(function (r) {

            var current_category = $("#category").attr("content");
            vue.current_category = current_category?current_category:"all";

            var url_s = get_url_parameter()
            vue.page = get_obj_value(url_s, "page", vue.page)

            if(!vue.current_category || vue.current_category == "all"){
                vue.current_category = vue.photo_nav;
            }else{
                vue.current_category = [vue.current_category]
            }
            get_global(vue.page, vue.current_category);
        });
    })

    function get_show_category(){

        var conditions = [
             {
                type:"text",
                names:["photo-page-nav"],
                result_key:"photo_nav"
             }

        ];
        var d ={
            conditions:JSON.stringify(conditions),
            theme_name:"osr-theme-w"
        }

        var result = osrHttp("GET","/api/global/theme-data/display", d, args={not_prompt:true});
        result.then(function (r) {

            var photo_nav = r.data.medias.photo_nav.length===0?null:r.data.medias.photo_nav[0];
            if(photo_nav.code && photo_nav.code_type=="html"){
                vue.photo_nav = JSON.parse(photo_nav.code);
            }else{
                vue.photo_nav = photo_nav.code;
            }
        });

        return result;
    }

    function get_global(page, category_name){
        vue.page = page;
        vue.current_category = category_name;
        var d ={
            category_type:"image",
            category_name:JSON.stringify(vue.current_category),
            page:vue.page,
            pre:12
        }

        var result = osrHttp("GET","/api/global/media", d, args={not_prompt:true});

        result.then(function (r) {
            vue.photos = r.data.medias;
            vue.pages = paging(page_total=vue.photos.page_total, current_page=vue.photos.current_page);
        });

        if(vue.current_category.length < 2){
            var temp_category = vue.current_category[0];
        }else{
            var temp_category = "all";
        }

        var url = window.location.pathname
                    +"?category="+temp_category
                    +"&page="+page
        history_state(null, url);
    }

    //初始化图片查看器
    var is_init_viewer = false;
    function init_viewer(id) {
        id = id?id:"galley";
        if(!is_init_viewer){
            var $images = $('#'+id);
            $images.on({}).viewer({
                interval:2500
            });
            is_init_viewer = true;
        }
        $('#'+id).on({}).viewer('update');
    }


