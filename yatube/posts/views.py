from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Comment, Follow
from .settings import NUMBER_POSTS


def get_page(page_number, posts):
    paginator = Paginator(posts, NUMBER_POSTS)
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    posts = Post.objects.all()
    page_obj = get_page(request.GET.get('page'), posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group).all()
    page_obj = get_page(request.GET.get('page'), posts)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    follow = False
    author = get_object_or_404(User, username=username)
    if request.user.is_authenticated:
        follow = Follow.objects.filter(
            user=request.user.id, author=author.id).exists()
    posts = author.posts.all()
    page_obj = get_page(request.GET.get('page'), posts)
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': follow
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'comments': Comment.objects.filter(post=post),
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if not form.is_valid():
        template = 'posts/create_post.html'
        context = {'form': form}
        return render(request, template, context)
    create_post = form.save(commit=False)
    create_post.author = request.user
    create_post.save()
    return redirect('posts:profile', request.user.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    # Получите пост и сохраните его в переменную post.
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follow = Follow.objects.filter(user=request.user)
    follow_authors = [entry.author for entry in follow]
    posts = Post.objects.filter(author__in=follow_authors)
    page_obj = get_page(request.GET.get('page'), posts)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow_exists = Follow.objects.filter(
        user=request.user, author=author).exists()
    if author != request.user and not follow_exists:
        Follow(user=request.user, author=author).save()
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, user=request.user, author=author)
    follow.delete()
    return redirect('posts:profile', username=username)
