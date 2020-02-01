from dp.data.music import MusicMediums


def test_musicmediums_load_multi_ppm():
    m = MusicMediums.from_dict({
        'ppm': 'saxophone, jazz saxophone'
    })

    assert m.ppm == tuple(['saxophone', 'jazz saxophone'])


def test_musicmediums_load_multi_ppm_trims():
    m = MusicMediums.from_dict({
        'ppm': 'saxophone,  jazz saxophone'
    })

    assert m.ppm == tuple(['saxophone', 'jazz saxophone'])
