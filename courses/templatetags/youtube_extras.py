from django import template
import re

register = template.Library()

def youtube_id(url):
    """
    Ekstrak ID video dari URL YouTube (youtube.com atau youtu.be)
    """
    if not url:
        return ''
    # Cek pola youtu.be/xxxx
    match = re.search(r'youtu\.be/([\w-]+)', url)
    if match:
        return match.group(1)
    # Cek pola v=xxxx
    match = re.search(r'v=([\w-]+)', url)
    if match:
        return match.group(1)
    # Cek pola embed/xxxx
    match = re.search(r'embed/([\w-]+)', url)
    if match:
        return match.group(1)
    return ''

register.filter('youtube_id', youtube_id) 