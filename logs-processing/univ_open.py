def univ_open(file_path, mode='r'):
    # If the file ends with ".gz" then open it through GZip
    if file_path.split('.')[-1].lower() == 'gz':
        from gzip import open as gzopen
        if mode in ('w', 'wb', 'w+', 'wb+'):
            return gzopen(file_path, mode, 6)
        else:
            return gzopen(file_path, mode)
    else:
        return open(file_path, mode)

