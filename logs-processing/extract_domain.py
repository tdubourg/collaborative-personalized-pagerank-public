def extract_domain(url):
    try:
        url = url[url.index("//")+2:] # getting rid of protocol://
    except ValueError:
        # There was no protocol specified
        pass
    try:
        url = url[:url.index("/")] # getting rid of everything after the first "/"
    except ValueError:
        # Maybe it was a domain-only url, with no "/"
        pass
    return url