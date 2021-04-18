#!/bin/python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2021 Sean Anderson <seanga2@gmail.com>

from getopt import getopt, GetoptError
import sys
from itertools import chain, islice
from json import load
from jinja2 import Environment, FileSystemLoader, select_autoescape
from numpy import array_split
from random import shuffle
from requests_html import HTMLSession

env = Environment(
    loader=FileSystemLoader("."),
    autoescape=select_autoescape(['html', 'xml'])
)

def weighted(white, blue, black, red, green, gold, colorless):
    # Grab n random cards and put them into multicolor
    n = 13
    multicolor = list(chain(white[:n], blue[:n], black[:n], red[:n], green[:n], gold, colorless))
    shuffle(multicolor)

    # Then shuffle the multicolor back into the colored piles, and shuffle
    # This yields "weighted" piles
    (white, blue, black, red, green) = \
            ([*l, *m] for (l, m) in zip((white[n:], blue[n:], black[n:], red[n:], green[n:]), array_split(multicolor, 5)))

    if False:
        white = ["Land Tax"] * 72
        blue = ["Opt"] * 72
        black = ["Pack Rat"] * 72
        red = ["Abrade"] * 72
        green = ["Explore"] * 72

    for l in (white, blue, black, red, green):
        shuffle(l)

    # Give each player 9 packs of 5 (one from each weighted pile)
    player = array_split(list(zip(white, blue, black, red, green)), 8)
    # Form 5 packs, where each pack is 1 of the 5-card packs plus 4 cards from the remaining packs
    return [
                [
                    [*wholes, *parts.tolist()]
                    for (wholes, parts) in zip(packs[:5], array_split(list(chain(*packs[5:])), 5))
                ]
                for packs in player
           ]

def guaranteed(white, blue, black, red, green, gold, colorless):
    # Make a big pile of all the cards (except the ones guaranteed to be in each pack)
    n = 5 * 8
    multicolor = list(chain(white[n:], blue[n:], black[n:], red[n:], green[n:], gold, colorless))
    shuffle(multicolor)

    # Remove the cards used for multicolor above
    (white, blue, black, red, green) = (white[:n], blue[:n], black[:n], red[:n], green[:n])

    return [player.tolist()
            for player in array_split([list(cards)
                for cards in zip(white, blue, black, red, green, *(multi.tolist()
                    for multi in array_split(multicolor, 4)
                ))
            ], 8)
        ]

def usage():
    print("Usage: %s [OPTION] URL" % sys.argv[0])
    print("Create [0-7].html with packs for a \"rectangle\" draft")
    print("\t-g Guarantee one card of each color in each pack (default).")
    print("\t-h Print this help message.")
    print("\t-w Use a weighted scheme to distribute cards.")

def main():
    try:
        opts, args = getopt(sys.argv[1:], 'gwh')
    except GetoptError as e:
        print(e)
        usage()
        sys.exit(2)
    weighted = False
    for o, a in opts:
        if o == '-g':
            weighted = False
        elif o == '-h':
            usage()
            sys.exit()
        elif o == '-w':
            weighted = True

    if len(args) != 1:
        print("Missing cube cobra url")
        usage()
        sys.exit(2)

    # Download and extract the cards from cube cobra
    resp = HTMLSession().get(args[0])
    cards = resp.html.render(script="() => {return window.reactProps}")

    # Set up the piles
    card_map = {}
    (white, blue, black, red, green, gold, colorless) = ([], [], [], [], [], [], [])
    for card in cards['cube']['cards']:
        colors = card['colors']
        name = card['details']['name']
        image = card['details']['image_normal']

        card_map[name] = image
        if colors == []:
            colorless.append(name)
        elif colors == ['W']:
            white.append(name)
        elif colors == ['U']:
            blue.append(name)
        elif colors == ['B']:
            black.append(name)
        elif colors == ['R']:
            red.append(name)
        elif colors == ['G']:
            green.append(name)
        else:
            gold.append(name)

    if False:
        white = ["Land Tax"] * 49
        blue = ["Opt"] * 49
        black = ["Pack Rat"] * 49
        red = ["Abrade"] * 49
        green = ["Explore"] * 49
        gold = ["Tundra"] * 70
        colorless = ["Smokestack"] * 45

    for l in (white, blue, black, red, green, gold, colorless):
        shuffle(l)

    # Shuffle
    if weighted:
        player = weighted(white, blue, black, red, green, gold, colorless)
    else:
        player = guaranteed(white, blue, black, red, green, gold, colorless)

    # Then shuffle everything so you can't tell which pack has more of any color
    for i in range(len(player)):
        for j in range(len(player[i])):
            shuffle(player[i][j])
        shuffle(player[i])

    template = env.get_template("pack.html")
    for (i, packs) in enumerate(player):
        with open("%s.html" % i, 'w') as f:
            f.write(template.render(i=i, packs=packs, card_map=card_map))

if __name__ == "__main__":
    main()
