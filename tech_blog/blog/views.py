import json
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Top, Article, ArticleTag
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def _get_page(list_, page_no, count=9):
    paginator = Paginator(list_, count)
    page_number = page_no
    try:
        page = paginator.page(page_no)
    except (EmptyPage, PageNotAnInteger):
        page_number = 1
        page = paginator.page(page_number)
    return page, int(page_number)


def index(request):

    if not request.GET.getlist('tag') or '' in request.GET.getlist('tag'):
        flag = "all"
        tag_names = []
        pages, page_number = _get_page(Article.objects.all().order_by(
                'created_date').reverse(), request.GET.get('page'))
    else:
        flag = "part"
        tag_names = request.GET.getlist('tag')
        tag_id = ArticleTag.objects.filter(name__in=request.GET.getlist('tag'))
        tags_id = [tag_id[i].id for i in range(len(tag_id))]

        if tags_id:
            pages, page_number = _get_page(Article.objects.filter(tags__in=tags_id).order_by(
                'created_date').reverse().distinct(), request.GET.get('page'))
        else:
            pages, page_number = _get_page(Article.objects.all().order_by(
                   'created_date').reverse(), request.GET.get('page'))

    display_max = 5
    total = pages.paginator.num_pages
    if page_number < 3:
        start = 1
        end = display_max if total > display_max else total
    elif page_number + 2 > total:
        start = total - display_max + 1 if total - display_max >= 1 else 1
        end = total
    else:
        start = page_number - 2 if page_number - 2 >= 1 else 1
        end = page_number + 2 if total > page_number + 2 else total

    next_num = None
    pre_num = None
    if pages.has_next():
        next_num = pages.next_page_number()

    if pages.has_previous():
        pre_num = pages.previous_page_number()

    top = Top.objects.filter(is_used=True).first()

    paging = {
        "next": next_num,
        "previous": pre_num,
        "range": range(start, end + 1),
        "current": page_number,
    }

    data = {
        'top': top,
        'page': pages,
        'tags': ArticleTag.objects.all(),
        'paging': paging,
        'flag': flag,
        'tag_names': tag_names, 
    }

    return render(request, 'news/index.html', data)


def article(request, article_id):

    tag_names = request.GET.getlist(
        'tag') if request.GET.getlist('tag') else None
    article = get_object_or_404(Article, id=article_id)

    writers = []
    writers.extend(article.employee.all())
    writers.extend(article.member.all())

    pages, page_number = _get_page(
        Article.objects.
        filter(tags__in=article.tags.all()).
        exclude(id=article.id).
        order_by('created_date').
        reverse().
        distinct(), request.GET.get('page'), count=3)

    try:
        article_content = json.dumps(article.article).rstrip("\"").lstrip("\"")
    except (ObjectDoesNotExist):
        article_content = None

    top = Top.objects.filter(is_used=True).first()

    data = {
        'top': top,
        'article': article,
        'writers': writers,
        'pages': pages,
        'article_content': article_content,
        'tag_names': tag_names,
    }

    return render(request, "news/article.html", data)
