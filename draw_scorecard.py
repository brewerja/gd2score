import svgwrite

ORIGIN_X, ORIGIN_Y = 10, 10
ATBAT_W, ATBAT_HT = 210, 20 
NAME_W = 100
TEXT_HOP = 5
SCORE_W = 25


def get_height(g):
    return sum([max(len(inning.top), len(inning.bottom))
                for inning in g.innings]) * ATBAT_HT


def draw(g, players):
    dwg = svgwrite.Drawing('test.svg', debug=True, profile='full')
    dwg.add_stylesheet('style.css', 'styling')

    dwg.add(dwg.rect((ORIGIN_X, ORIGIN_Y), (ATBAT_W, get_height(g))))
    dwg.add(dwg.rect((ORIGIN_X + ATBAT_W * 1.25, ORIGIN_Y),
            (ATBAT_W, get_height(g))))

    dwg.add(dwg.line((ORIGIN_X + NAME_W, ORIGIN_Y),
                     (ORIGIN_X + NAME_W, ORIGIN_Y + get_height(g))))
    dwg.add(dwg.line((ORIGIN_X + NAME_W + SCORE_W, ORIGIN_Y),
                     (ORIGIN_X + NAME_W + SCORE_W, ORIGIN_Y + get_height(g))))
    dwg.add(dwg.line((ORIGIN_X + ATBAT_W * 2.25 - NAME_W, ORIGIN_Y),
                     (ORIGIN_X + ATBAT_W * 2.25 - NAME_W,
                      ORIGIN_Y + get_height(g))))
    dwg.add(dwg.line((ORIGIN_X + ATBAT_W * 2.25 - NAME_W - SCORE_W, ORIGIN_Y),
                     (ORIGIN_X + ATBAT_W * 2.25 - NAME_W - SCORE_W,
                      ORIGIN_Y + get_height(g))))


    y = ORIGIN_Y + ATBAT_HT
    for inning in g.innings:
        inning_start_y = y
        for event in inning.top:
            dwg.add(dwg.text(players.get(event.batter),
                             x=[ORIGIN_X + NAME_W - TEXT_HOP],
                             y=[y - TEXT_HOP],
                             class_='batter-name', text_anchor='end'))
            dwg.add(dwg.text(event.scoring.code,
                             x=[ORIGIN_X + NAME_W + TEXT_HOP],
                             y=[y - TEXT_HOP], class_=event.scoring.result))
            y += ATBAT_HT
        inning_end_y = y
        y = inning_start_y
        for event in inning.bottom:
            dwg.add(dwg.text(players.get(event.batter),
                             x=[ORIGIN_X + ATBAT_W * 2.25 - NAME_W + TEXT_HOP],
                             y=[y - TEXT_HOP],
                             class_='batter-name'))
            dwg.add(dwg.text(event.scoring.code,
                             x=[ORIGIN_X + ATBAT_W * 2.25 - NAME_W - TEXT_HOP],
                             y=[y - TEXT_HOP], text_anchor='end',
                             class_=event.scoring.result))
            y += ATBAT_HT
        y = max(inning_end_y, y)

        dwg.add(dwg.line((ORIGIN_X, y - ATBAT_HT),
                         (ORIGIN_X + ATBAT_W, y - ATBAT_HT)))
        dwg.add(dwg.line((ORIGIN_X + ATBAT_W * 1.25, y - ATBAT_HT),
                         (ORIGIN_X + ATBAT_W * 1.25 + ATBAT_W, y - ATBAT_HT)))

    dwg.save()


if __name__ == '__main__':
    draw('hi')
