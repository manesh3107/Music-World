from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.db.models import Q,F
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count
from django.db import connection


# Create your views here.
def index(request):

    # Display recent songs
    if not request.user.is_anonymous:
        recent = list(Recent.objects.filter(
            user=request.user).values('song_id').order_by('-id'))
        recent_id = [each['song_id'] for each in recent][:6]
        recent_songs_unsorted = Song.objects.filter(
            id__in=recent_id, recent__user=request.user)
        recent_songs = list()
        for id in recent_id:
            recent_songs.append(recent_songs_unsorted.get(id=id))
    else:
        recent = None
        recent_songs = None

    first_time = False
    # Last played song
    if not request.user.is_anonymous:
        last_played_list = list(Recent.objects.filter(
            user=request.user).values('song_id').order_by('-id'))
        if last_played_list:
            last_played_id = last_played_list[0]['song_id']

            last_played_song = Song.objects.get(id=last_played_id)
        else:
            first_time = True
            last_played_song = Song.objects.get(id=18)

    else:
        first_time = True
        last_played_song = Song.objects.get(id=18)

    # Display all songs
    songs = Song.objects.all()

    # Display few songs on home page
    songs_all = list(Song.objects.all().values('id').order_by('?'))
    sliced_ids = [each['id'] for each in songs_all][:6]
    indexpage_songs = Song.objects.filter(id__in=sliced_ids)

    # Display Hindi Songs
    songs_hindi = list(Song.objects.filter(language='Hindi').values('id'))
    sliced_ids = [each['id'] for each in songs_hindi][:6]
    indexpage_hindi_songs = Song.objects.filter(id__in=sliced_ids)

    # Display English Songs
    songs_english = list(Song.objects.filter(language='English').values('id'))
    sliced_ids = [each['id'] for each in songs_english][:6]
    indexpage_english_songs = Song.objects.filter(id__in=sliced_ids)

    if len(request.GET) > 0:
        search_query = request.GET.get('q')
        filtered_songs = songs.filter(
            Q(name__icontains=search_query)).distinct()
        context = {'all_songs': filtered_songs,
                   'last_played': last_played_song, 'query_search': True}
        return render(request, 'musicapp/index.html', context)
    
    # Subquery to get the most liked songs
    songs_with_likes = Song.objects.annotate(like_counts=Count('like_count')).order_by('-like_count')[:6]

    context = {
        'all_songs': indexpage_songs,
        'recent_songs': recent_songs,
        'hindi_songs': indexpage_hindi_songs,
        'english_songs': indexpage_english_songs,
        'last_played': last_played_song,
        'first_time': first_time,
        'most_liked_songs': songs_with_likes,
        'query_search': False,
    }

    return render(request, 'musicapp/index.html', context)

def hindi_songs(request):
    hindi_songs = Song.objects.filter(language='Hindi')

    # Last played song
    last_played_list = list(Recent.objects.values('song_id').order_by('-id'))
    if last_played_list:
        last_played_id = last_played_list[0]['song_id']
        last_played_song = Song.objects.get(id=last_played_id)
    else:
        last_played_song = Song.objects.get(id=18)

    query = request.GET.get('q')

    if query:
        # Filter songs by name and language
        hindi_songs = hindi_songs.filter(Q(name__icontains=query)).distinct()

    context = {'hindi_songs': hindi_songs, 'last_played': last_played_song}
    return render(request, 'musicapp/hindi_songs.html', context=context)



def english_songs(request):

    english_songs = Song.objects.filter(language='English')

    # Last played song
    last_played_list = list(Recent.objects.values('song_id').order_by('-id'))
    if last_played_list:
        last_played_id = last_played_list[0]['song_id']
        last_played_song = Song.objects.get(id=last_played_id)
    else:
        last_played_song = Song.objects.get(id=18)

    query = request.GET.get('q')

    if query:
        english_songs = english_songs.filter(
            Q(name__icontains=query)).distinct()
        context = {'english_songs': english_songs}
        return render(request, 'musicapp/english_songs.html', context)

    context = {'english_songs': english_songs, 'last_played': last_played_song}
    return render(request, 'musicapp/english_songs.html', context=context)


@login_required(login_url='login')
def play_song(request, song_id):
    songs = Song.objects.filter(id=song_id).first()
    # Add data to recent database
    if list(Recent.objects.filter(song=songs, user=request.user).values()):
        data = Recent.objects.filter(song=songs, user=request.user)
        data.delete()
    data = Recent(song=songs, user=request.user)
    data.save()
    return redirect('all_songs')


@login_required(login_url='login')
def play_song_index(request, song_id):
    songs = Song.objects.filter(id=song_id).first()
    # Add data to recent database
    if list(Recent.objects.filter(song=songs, user=request.user).values()):
        data = Recent.objects.filter(song=songs, user=request.user)
        data.delete()
    data = Recent(song=songs, user=request.user)
    data.save()
    return redirect('index')


@login_required(login_url='login')
def play_recent_song(request, song_id):
    songs = Song.objects.filter(id=song_id).first()
    # Add data to recent database
    if list(Recent.objects.filter(song=songs, user=request.user).values()):
        data = Recent.objects.filter(song=songs, user=request.user)
        data.delete()
    data = Recent(song=songs, user=request.user)
    data.save()
    return redirect('recent')


def all_songs(request):
    songs = Song.objects.all()

    first_time = False
    last_played_song = None  # Initialize it to None by default

    # Last played song
    if not request.user.is_anonymous:
        last_played_list = list(Recent.objects.filter(
            user=request.user).values('song_id').order_by('-id'))
        if last_played_list:
            last_played_id = last_played_list[0]['song_id']
            last_played_song = Song.objects.get(id=last_played_id)
    else:
        first_time = True

    # Rest of your code ...
    qs_singers = Song.objects.values_list('singer').all()
    s_list = [s.split(',') for singer in qs_singers for s in singer]
    all_singers = sorted(
        list(set([s.strip() for singer in s_list for s in singer])))
    qs_languages = Song.objects.values_list('language').all()
    all_languages = sorted(
        list(set([l.strip() for lang in qs_languages for l in lang])))

    if len(request.GET) > 0:
        search_query = request.GET.get('q')
        search_singer = request.GET.get('singers') or ''
        search_language = request.GET.get('languages') or ''
        filtered_songs = songs.filter(Q(name__icontains=search_query)).filter(
            Q(language__icontains=search_language)).filter(Q(singer__icontains=search_singer)).distinct()
        context = {
            'songs': filtered_songs,
            'last_played': last_played_song,
            'all_singers': all_singers,
            'all_languages': all_languages,
            'query_search': True,
        }
        return render(request, 'musicapp/all_songs.html', context)

    context = {
        'songs': songs,
        'last_played': last_played_song,
        'first_time': first_time,
        'all_singers': all_singers,
        'all_languages': all_languages,
        'query_search': False,
    }
    return render(request, 'musicapp/all_songs.html', context=context)


def recent(request):

    # Last played song
    last_played_list = list(Recent.objects.values('song_id').order_by('-id'))
    if last_played_list:
        last_played_id = last_played_list[0]['song_id']
        last_played_song = Song.objects.get(id=last_played_id)
    else:
        last_played_song = Song.objects.get(id=18)

    # Display recent songs
    recent = list(Recent.objects.filter(user=request.user).values('song_id').order_by('-id'))
    if recent and not request.user.is_anonymous:
        recent_id = [each['song_id'] for each in recent]
        recent_songs_unsorted = Song.objects.filter(
            id__in=recent_id, recent__user=request.user)
        recent_songs = list()
        for id in recent_id:
            recent_songs.append(recent_songs_unsorted.get(id=id))
    else:
        recent_songs = None

    if len(request.GET) > 0:
        search_query = request.GET.get('q')
        filtered_songs = recent_songs_unsorted.filter(
            Q(name__icontains=search_query)).distinct()
        context = {'recent_songs': filtered_songs,
                   'last_played': last_played_song, 'query_search': True}
        return render(request, 'musicapp/recent.html', context)

    context = {'recent_songs': recent_songs,
               'last_played': last_played_song, 'query_search': False}
    return render(request, 'musicapp/recent.html', context=context)


@login_required(login_url='login')
def detail(request, song_id):
    songs = Song.objects.filter(id=song_id).first()

    # Add data to recent database
    if list(Recent.objects.filter(song=songs, user=request.user).values()):
        data = Recent.objects.filter(song=songs, user=request.user)
        data.delete()
    data = Recent(song=songs, user=request.user)
    data.save()

    # Last played song
    last_played_list = list(Recent.objects.values('song_id').order_by('-id'))
    if last_played_list:
        last_played_id = last_played_list[0]['song_id']
        last_played_song = Song.objects.get(id=last_played_id)
    else:
        last_played_song = Song.objects.get(id=18)

    playlists = Playlist.objects.filter(
        user=request.user).values('playlist_name').distinct
    is_favourite = Favourite.objects.filter(
        user=request.user).filter(song=song_id).values('is_fav')

    if request.method == "POST":
        if 'playlist' in request.POST:
            playlist_name = request.POST["playlist"]
            # Check if the song is already in the selected playlist
            existing_entry = Playlist.objects.filter(
                user=request.user, song=songs, playlist_name=playlist_name).first()
            if existing_entry:
                messages.warning(request, "Song is already in this playlist.")
            else:
                q = Playlist(user=request.user, song=songs, playlist_name=playlist_name)
                q.save()
                messages.success(request, "Song added to playlist!")
        elif 'add-fav' in request.POST:
            is_fav = True
            query = Favourite(user=request.user, song=songs, is_fav=is_fav)
            query.save()
            messages.success(request, "Added to favorite!")
            return redirect('detail', song_id=song_id)
        elif 'rm-fav' in request.POST:
            is_fav = True
            query = Favourite.objects.filter(
                user=request.user, song=songs, is_fav=is_fav)
            query.delete()
            messages.success(request, "Removed from favorite!")
            return redirect('detail', song_id=song_id)

    context = {'songs': songs, 'playlists': playlists,
               'is_favourite': is_favourite, 'last_played': last_played_song}
    return render(request, 'musicapp/detail.html', context=context)



def mymusic(request):
    return render(request, 'musicapp/mymusic.html')


def playlist(request):
    playlists = Playlist.objects.filter(
        user=request.user).values('playlist_name').distinct()
    context = {'playlists': playlists}
    return render(request, 'musicapp/playlist.html', context=context)


def playlist_songs(request, playlist_name):
    songs = Song.objects.filter(
        playlist__playlist_name=playlist_name, playlist__user=request.user).distinct()

    if request.method == "POST":
        song_id = list(request.POST.keys())[1]
        playlist_song = Playlist.objects.filter(
            playlist_name=playlist_name, song__id=song_id, user=request.user)
        playlist_song.delete()
        messages.success(request, "Song removed from playlist!")

    context = {'playlist_name': playlist_name, 'songs': songs}

    return render(request, 'musicapp/playlist_songs.html', context=context)


#for favourite page songs and remove from that list
def favourite(request):
    songs = Song.objects.filter(
        favourite__user=request.user, favourite__is_fav=True).distinct()
    print(f'songs: {songs}')

    if request.method == "POST":
        song_id = list(request.POST.keys())[1]
        favourite_song = Favourite.objects.filter(
            user=request.user, song__id=song_id, is_fav=True)
        favourite_song.delete()
        messages.success(request, "Removed from favourite!")
    context = {'songs': songs}
    return render(request, 'musicapp/favourite.html', context=context)


from django.http import JsonResponse

def like_song(request, song_id):
    song = get_object_or_404(Song, pk=song_id)
    user = request.user

    if user in song.liked_by_users.all():
        # User has already liked the song, so unlike it
        song.liked_by_users.remove(user)
        liked = False
    else:
        # User has not liked the song, so like it
        song.liked_by_users.add(user)
        liked = True

    like_count = song.liked_by_users.count()

    # Update the like count in the song model
    song.like_count = like_count
    song.save()

    return JsonResponse({'liked': liked, 'like_count': like_count})


