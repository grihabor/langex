import gzip
import json
from urllib.parse import urljoin

import click
import itertools
from typing import Optional, List, NamedTuple, Dict, Tuple, Iterable

from bs4 import BeautifulSoup
import requests


def template(i: int):
    base = "https://en.language.exchange/online/"
    if i == 1:
        return base
    else:
        return urljoin(base, str(i)) + '/'


@click.command()
@click.option('-d', '--headers')  # -h is reserved for --help
@click.option('-b', '--begin', default=1)
@click.option('-e', '--end', default=1)
def main(headers, begin, end):
    with open(headers, 'r') as f:
        h = (dict(parse_headers(f)) if headers else None)

    total : List[Person] = []

    def done(i):
        click.echo("Done {} pages".format(i - 1), err=True)
        click.echo(json.dumps([
            p._asdict()
            for p in total
        ]))
        return None

    for i in itertools.count(begin):
        if i == end:
            return done(i)

        page = get_page(i, headers=h)
        if page is None:
            return done(i)

        parsed = parse_page(page)
        total.extend(parsed)


def parse_headers(lines) -> Iterable[Tuple[str, str]]:
    for line in lines:
        parts = line.split(':', 1)
        if len(parts) != 2:
            raise ValueError("failed to parse headers file: {}".format(line))

        yield (parts[0].strip(), parts[1].strip())


def get_page(i: int, headers: Dict[str, str]) -> Optional[bytes]:
    url = template(i)
    click.echo("url: {}".format(url), err=True)
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return None

    content = r.content
    # try:
    #     content = gzip.decompress(content)
    # except:
    #     click.echo("bad gzip file", err=True)

    return content


def parse_page(page: bytes) -> 'Optional[List[Person]]':
    bs = BeautifulSoup(page, features='html.parser')
    main_blocks = bs.find_all('article', {'class': 'entry'})
    if len(main_blocks) != 1:
        click.echo("expect 1 main block, got {}".format(len(main_blocks)), err=True)
        return None

    main_block = main_blocks[0]
    items = list(main_block.children)
    click.echo("item list: {}".format(len(items)), err=True)
    persons = []
    for item in items:
        person = parse_person(item)
        if person is None:
            continue
        persons.append(person)
    return persons


def parse_person(item):
    if not hasattr(item, 'children'):
        return None

    item_parts = list(item.children)
    item_parts = [p for p in item_parts if hasattr(p, 'tag')]

    if len(item_parts) != 2:
        click.echo("item must have 2 parts, got {}".format(len(item_parts)), err=True)
        return None

    image, text = item_parts
    text_parts = list(text.children)
    text_parts = [p for p in text_parts if hasattr(p, 'tag')]

    if len(text_parts) != 4:
        click.echo("text must have 4 parts, got {}".format(len(text_parts)), err=True)
        return None

    name_block, location_block, lang_block, desc_block = text_parts
    name_a = list(name_block.find_all('a'))
    if len(name_a) != 1:
        click.echo("name block must have 1 a tag, got {}".format(len(name_a)), err=True)
        return None

    location_a = list(location_block.find_all('a'))
    if len(location_a) == 0 or len(location_a) > 2:
        click.echo("location block must have 1 or 2 a tags, got {}".format(len(location_a)), err=True)
        return None

    if len(location_a) == 2:
        city, country = location_a
        city, country = city.text, country.text
    else:
        city, country = None, location_a[0].text

    lang_columns = list(lang_block.find('tr').find_all('td', recursive=False))
    if len(lang_columns) != 3:
        click.echo("lang block must have 3 columns, got {}".format(len(lang_columns)), err=True)
        return None

    speaks = [a.text.strip() for a in lang_columns[0].find_all('a')]
    looks_for = [a.text.strip() for a in lang_columns[2].find_all('a')]

    return Person(
        name=name_a[0].text,
        city=city,
        country=country,
        speaks=speaks,
        looks_for=looks_for,
        url=name_a[0]['href'],
    )


class Person(NamedTuple):
    name: str
    city: str
    country: str
    speaks: List[str]
    looks_for: List[str]
    url: str
