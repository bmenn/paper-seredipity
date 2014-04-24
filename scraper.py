from bs4 import BeautifulSoup
import urllib2
import urlparse


def fetch(doi, get_citations=True):
    url = "http://citeseerx.ist.psu.edu/viewdoc/summary?doi="
    url += doi

    doc = parse_summary(url, get_citations)
    doc.update({'doi': doi,
                'id': 'doi:' + doi})

    return doc


def parse_div_result(url, limit=0):
    page = BeautifulSoup(urllib2.urlopen(url).read())

    divs = page.select('.result')
    results = []

    for d in divs:
        title_html = d.h3.a.stripped_strings
        authors_html = d.select('.authors')
        date_html = d.select('.pubyear')
        link = d.h3.a['href']

        title = ' '.join(title_html)
        if authors_html:
            authors = ''.join(authors_html[0].stripped_strings).strip('by \n')
        else:
            authors = ''
        if date_html:
            date = ''.join(date_html[0].stripped_strings).strip(', ')
        else:
            date = ''

        query_values = get_query_values(link)
        if 'doi' in query_values:
            doi = query_values['doi'][0]
        else:
            doi = ''
        if 'rank' in query_values:
            rank = query_values['rank'][0]
        else:
            rank = -1

        results.append({'title': title,
                        'authors': authors,
                        'date': date,
                        'link': link,
                        'doi': doi,
                        'rank': rank
                        })

    if limit > 10:
        next_url = ("http://citeseerx.ist.psu.edu"
                    + page.select('#pager')[0].a['href'])
        results.extend(parse_div_result(next_url, limit=limit - 10))

    if limit == 0:
        return results
    else:
        return results[:limit]


def parse_summary(url, get_citations=True):
    summary = {'abstract': 'Not available',
               'authors': 'Not available',
               'date': 'Not available',
               'title': 'Not available',
               'citations': [],
               'cited by': []
               }
    try:
        page = BeautifulSoup(urllib2.urlopen(url).read())
    except urllib2.HTTPError:
        return summary

    abstract_html = page.find('meta', attrs={'name': 'description'})
    title_html = page.find('meta', attrs={'name': 'citation_title'})
    authors_html = page.find('meta', attrs={'name': 'citation_authors'})
    date_html = page.find('meta', attrs={'name': 'citation_year'})
    citation_html = page.select('#citations a')
    cited_by_link = page.find('a', attrs={'title': 'number of citations'})

    if abstract_html:
        summary['abstract'] = abstract_html['content'].strip()
    if title_html:
        summary['title'] = title_html['content'].strip()
    if authors_html:
        summary['authors'] = authors_html['content'].strip()
    if date_html:
        summary['date'] = date_html['content'].strip()

    if get_citations:
        for e in citation_html:
            if ('class' in e.attrs) and ('citation_only' in e['class']):
                # Publication is not in CiteSeerX. Stuck with cid for identifier
                start_ind = e['href'].find('cid=')
                if start_ind != -1:
                    summary['citations'].append(e['href'][start_ind:].replace('=', ':'))
                else:
                    continue
            else:
                # cid is useless for retrieving publication metadata
                # Get the redirect url and scape it out
                cite_url = "http://citeseerx.ist.psu.edu" + e['href']
                redirect_url = urllib2.urlopen(cite_url).geturl()

                query_values = get_query_values(redirect_url)

                if 'doi' in query_values:
                    summary['citations'].append('doi:' + query_values['doi'][0])
                else:
                    continue

        if not (cited_by_link is None):
            cited_by_results = parse_div_result('http://citeseerx.ist.psu.edu'
                                                + cited_by_link['href'])
            for e in cited_by_results:
                summary['cited by'].append('doi:' + e['doi'])

    return summary


def get_query_values(url):
    o = urlparse.urlparse(url)
    return urlparse.parse_qs(o.query)


def search(q):
    url = "http://citeseerx.ist.psu.edu/search?q="
    url += q.replace(" ", "+")

    results = parse_div_result(url, limit=5)

    return results
