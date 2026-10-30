from bs4 import BeautifulSoup

from scraper_with_list_info import extraire_ville_liste


def _extraire(html):
    soupe = BeautifulSoup(html, 'html.parser')
    return extraire_ville_liste(soupe.div, soupe.div.get_text())


def test_structure_span_formula():
    html = (
        '<div><span class="formula J_formula"><a href="javascript:__doPostBack(1,\'Redisplay|1,,87\')">'
        '376-380 Rue St-Étienne</a></span><span class="formula J_formula">'
        '<a href="javascript:__doPostBack(1,\'Redisplay|1,,87\')">La Malbaie</a></span></div>'
    )
    assert _extraire(html) == ('La Malbaie', 'La Malbaie')


def test_structure_b_avec_arrondissement():
    html = (
        '<div><b><a href="javascript:__doPostBack(1,\'Redisplay|1\')">16 Rue Couillard</a></b>'
        '<b><a href="javascript:__doPostBack(1,\'Redisplay|1\')">Québec (La Cité-Limoilou)</a></b></div>'
    )
    assert _extraire(html) == ('Québec', 'La Cité-Limoilou')


def test_aucun_lien():
    assert _extraire('<div>rien</div>') == (None, None)
