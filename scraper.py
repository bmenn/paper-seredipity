from bs4 import BeautifulSoup
import urllib2
import urlparse


def fetch(doi):
    url = "http://citeseerx.ist.psu.edu/viewdoc/summary?doi="
    url += doi

    page = BeautifulSoup(urllib2.urlopen(url).read())
    doc = parse_summary(page)
    doc.update({'doi': doi})

    return doc


def parse_div_result(page):
    divs = page.select('.result')
    results = []

    for d in divs:
        title = d.h3.a.stripped_strings
        link = d.h3.a['href']
        authors = d.select('.authors')
        date = d.select('.pubyear')

        title = ' '.join(title)
        o = urlparse.urlparse(link)
        queries = urlparse.parse_qs(o.query)
        if queries['doi']:
            doi = queries['doi'][0]
        else:
            doi = ''
        if queries['rank']:
            rank = queries['rank'][0]
        else:
            rank = -1
        if authors:
            authors = ''.join(authors[0].stripped_strings).strip('by \n')
        else:
            authors = ''
        if date:
            date = ''.join(date[0].stripped_strings).strip(', ')
        else:
            date = ''

        results.append({'title': title,
                        'authors': authors,
                        'date': date,
                        'link': link,
                        'doi': doi,
                        'rank': rank
                        })

    return results


def parse_summary(page):
    abstract = page.find('meta', attrs={'name':'description'})
    title = page.find('meta', attrs={'name':'citation_title'})
    authors = page.find('meta', attrs={'name':'citation_authors'})
    date = page.find('meta', attrs={'name':'citation_year'})

    if abstract:
        abstract = abstract['content']
    else:
        abstract = ''
    if title:
        title = title['content']
    else:
        title = ''
    if authors:
        authors = authors['content']
    else:
        authors = ''
    if date:
        date = date['content']
    else:
        date = ''
    return {'abstract': abstract,
            'title': title,
            'authors': authors,
            'date': date
            }


def search(q):
    url = "http://citeseerx.ist.psu.edu/search?q="
    url += q.replace(" ", "+")

    page = BeautifulSoup(urllib2.urlopen(url).read())
    results = parse_div_result(page)

    return results
