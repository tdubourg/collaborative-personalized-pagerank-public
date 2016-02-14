from univ_open import univ_open

def load(path):
    with univ_open(path, 'r') as f:
        return dict(
            (map(int, l.strip().split(' ')) for l in f)
        )
