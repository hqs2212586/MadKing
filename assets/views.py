from django.shortcuts import render, HttpResponse
from assets import core, models, asset_handle, utils, admin
import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from assets import tables
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from assets.dashboard import  AssetDashboard

# Create your views here.


@login_required
def index(request):
    return render(request, 'index.html')


@csrf_exempt
# @utils.token_required
def asset_report(request):
    if request.method == 'POST':
        ass_handler = core.Asset(request)
        if ass_handler.data_is_valid():   # 判断数据是否valid
            print("----asset data valid:")
            ass_handler.data_inject()     # 是valid直接注入
            res = ass_handler.get_asset_id_by_sn()
            # return HttpResponse(json.dumps(ass_handler.response))

        return HttpResponse(json.dumps(ass_handler.response))
        # return render(request,'assets/asset_report_test.html',{'response':ass_handler.response})
        # else:
        # return HttpResponse(json.dumps(ass_handler.response))

    return HttpResponse('--test--')


@csrf_exempt
def asset_with_no_asset_id(request):
    if request.method == 'POST':
        print(request.POST.get("asset_data"))
        ass_handler = core.Asset(request)      # 实例化Asset类
        res = ass_handler.get_asset_id_by_sn()

        # return render(request,'assets/acquire_asset_id_test.html',{'response':res})
        return HttpResponse(json.dumps(res))


def new_assets_approval(request):
    """新资产批准"""
    if request.method == 'POST':
        # post请求提交form表单
        print('post', request.POST) # <QueryDict: {'csrfmiddlewaretoken': ['w6...IW'], 'approved_asset_list': ['1']}>
        # request.POST是一个只读字典，不能做修改
        request.POST = request.POST.copy()  # 为了修改这个字典，复制一份新的

        # 将数据从临时表中取出
        approved_asset_list = request.POST.getlist('approved_asset_list')
        approved_asset_list = models.NewAssetApprovalZone.objects.filter(id__in=approved_asset_list)

        response_dic = {}
        for obj in approved_asset_list:   # 循环存入数据
            request.POST['asset_data'] = obj.data   # 将资产数据加入request.post里是为了兼容命令行和浏览器
            ass_handler = core.Asset(request)
            if ass_handler.data_is_valid_without_id():  # 确认是否新资产
                ass_handler.data_inject()   # 数据注入数据库
                obj.approved = True    # 调整资产为已批准
                obj.save()

            response_dic[obj.id] = ass_handler.response
        return render(request, 'assets/new_assets_approval.html',
                      {'new_assets': approved_asset_list, 'response_dic': response_dic})
    else:
        # 处理get请求
        ids = request.GET.get('ids')
        id_list = ids.split(',')
        # __in :存在于一个list范围内
        new_assets = models.NewAssetApprovalZone.objects.filter(id__in=id_list)
        return render(request, 'assets/new_assets_approval.html', {'new_assets': new_assets})


def asset_report_test(request):
    return render(request, 'assets/asset_report_test.html')


@login_required
def acquire_asset_id_test(request):
    return render(request, 'assets/acquire_asset_id_test.html')


@login_required
def asset_list(request):
    print(request.GET)
    asset_obj_list = tables.table_filter(request, admin.AssetAdmin, models.Asset)
    # asset_obj_list = models.Asset.objects.all()
    print("asset_obj_list:", asset_obj_list)
    order_res = tables.get_orderby(request, asset_obj_list, admin.AssetAdmin)
    # print('----->',order_res)
    paginator = Paginator(order_res[0], admin.AssetAdmin.list_per_page)
    page = request.GET.get('page')
    try:
        asset_objs = paginator.page(page)
    except PageNotAnInteger:
        asset_objs = paginator.page(1)
    except EmptyPage:
        asset_objs = paginator.page(paginator.num_pages)
    table_obj = tables.TableHandler(request,
                                    models.Asset,
                                    admin.AssetAdmin,
                                    asset_objs,
                                    order_res
                                    )
    return render(request, 'assets/assets.html', {'table_obj': table_obj,
                                                  'paginator': paginator})


@login_required
def get_asset_list(request):
    asset_dic = asset_handle.fetch_asset_list()
    print(asset_dic)

    return HttpResponse(json.dumps(asset_dic, default=utils.json_date_handler))


@login_required
def asset_category(request):
    category_type = request.GET.get("category_type")
    if not category_type: category_type = 'server'
    if request.is_ajax():
        categories = asset_handle.AssetCategroy(request)
        data = categories.serialize_data()
        return HttpResponse(data)
    else:
        return render(request, 'assets/asset_category.html', {'category_type': category_type})


@login_required
def asset_event_logs(request, asset_id):
    if request.method == "GET":
        log_list = asset_handle.fetch_asset_event_logs(asset_id)
        return HttpResponse(json.dumps(log_list, default=utils.json_datetime_handler))


@login_required
def asset_detail(request, asset_id):
    if request.method == "GET":
        try:
            asset_obj = models.Asset.objects.get(id=asset_id)

        except ObjectDoesNotExist as e:
            return render(request, 'assets/asset_detail.html', {'error': e})
        return render(request, 'assets/asset_detail.html', {"asset_obj": asset_obj})


@login_required
def get_dashboard_data(request):
    '''返回主页面数据'''

    dashboard_data = AssetDashboard(request)
    dashboard_data.searilize_page()
    return HttpResponse(json.dumps(dashboard_data.data))


@login_required
def event_center(request):
    '''事件中心'''

    eventlog_objs = tables.table_filter(request, admin.EventLogAdmin, models.EventLog)
    # asset_obj_list = models.Asset.objects.all()
    #print("asset_obj_list:", asset_obj_list)
    order_res = tables.get_orderby(request, eventlog_objs, admin.EventLogAdmin)
    # print('----->',order_res)
    paginator = Paginator(order_res[0], admin.EventLogAdmin.list_per_page)

    page = request.GET.get('page')
    try:
        objs = paginator.page(page)
    except PageNotAnInteger:
        objs = paginator.page(1)
    except EmptyPage:
        objs = paginator.page(paginator.num_pages)

    table_obj = tables.TableHandler(request,
                                    models.EventLog,
                                    admin.EventLogAdmin,
                                    objs,
                                    order_res
                                    )


    return render(request,'assets/event_center.html',{'table_obj': table_obj,
                                                  'paginator': paginator})

