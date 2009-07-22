from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, get_host
from django.template import RequestContext
from django.db.models import Q
from django.http import Http404
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from photologue.models import *
from photos.models import Image
from photos.forms import PhotoUploadForm, PhotoEditForm


def upload(request, form_class=PhotoUploadForm,
        template_name="photos/upload.html"):
    """
    upload form for photos
    """
    photo_form = form_class()
    if request.method == 'POST':
        if request.POST.get("action") == "upload":
            photo_form = form_class(request.user, request.POST, request.FILES)
            if photo_form.is_valid():
                photo = photo_form.save(commit=False)
                photo.member = request.user
                photo.save()
                request.user.message_set.create(message=_("Successfully uploaded photo '%s'") % photo.title)
                return HttpResponseRedirect(reverse('photo_details', args=(photo.id,)))

    return render_to_response(template_name, {
        "photo_form": photo_form,
    }, context_instance=RequestContext(request))
upload = login_required(upload)

def yourphotos(request, template_name="photos/yourphotos.html"):
    """
    photos for the currently authenticated user
    """
    photos = Image.objects.filter(member=request.user).order_by("-date_added")
    return render_to_response(template_name, {
        "photos": photos,
    }, context_instance=RequestContext(request))
yourphotos = login_required(yourphotos)

def photos(request, template_name="photos/latest.html"):
    """
    latest photos
    """
    photos = Image.objects.filter(
        Q(is_public=True) |
        Q(is_public=False, member=request.user)
    ).order_by("-date_added")
    return render_to_response(template_name, {
        "photos": photos,
    }, context_instance=RequestContext(request))
photos = login_required(photos)

def details(request, id, template_name="photos/details.html"):
    """
    show the photo details
    """
    photo = get_object_or_404(Image, id=id)
    # @@@: test
    if not photo.is_public and request.user != photo.member:
        raise Http404
    photo_url = photo.get_display_url()
    
    title = photo.title
    host = "http://%s" % get_host(request)
    if photo.member == request.user:
        is_me = True
    else:
        is_me = False
    
    return render_to_response(template_name, {
        "host": host, 
        "photo": photo,
        "photo_url": photo_url,
        "is_me": is_me,
    }, context_instance=RequestContext(request))
details = login_required(details)

def memberphotos(request, username, template_name="photos/memberphotos.html"):
    """
    Get the members photos and display them
    """
    user = get_object_or_404(User, username=username)
    photos = Image.objects.filter(member__username=username, is_public=True).order_by("-date_added")
    return render_to_response(template_name, {
        "photos": photos,
    }, context_instance=RequestContext(request))
memberphotos = login_required(memberphotos)

def edit(request, id, form_class=PhotoEditForm,
        template_name="photos/edit.html"):
    photo = get_object_or_404(Image, id=id)
    photo_url = photo.get_display_url()

    if request.method == "POST":
        if photo.member != request.user:
            request.user.message_set.create(message="You can't edit photos that aren't yours")
            return HttpResponseRedirect(reverse('photo_details', args=(photo.id,)))
        if request.POST["action"] == "update":
            photo_form = form_class(request.user, request.POST, instance=photo)
            if photo_form.is_valid():
                photoobj = photo_form.save(commit=False)
                photoobj.save()
                request.user.message_set.create(message=_("Successfully updated photo '%s'") % photo.title)
                                
                return HttpResponseRedirect(reverse('photo_details', args=(photo.id,)))
        else:
            photo_form = form_class(instance=photo)

    else:
        photo_form = form_class(instance=photo)

    return render_to_response(template_name, {
        "photo_form": photo_form,
        "photo": photo,
        "photo_url": photo_url,
    }, context_instance=RequestContext(request))
edit = login_required(edit)

def destroy(request, id):
    photo = Image.objects.get(pk=id)
    title = photo.title
    if photo.member != request.user:
        request.user.message_set.create(message="You can't delete photos that aren't yours")
        return HttpResponseRedirect(reverse("photos_yours"))

    if request.method == "POST" and request.POST["action"] == "delete":
        photo.delete()
        request.user.message_set.create(message=_("Successfully deleted photo '%s'") % title)
    return HttpResponseRedirect(reverse("photos_yours"))
destroy = login_required(destroy)
