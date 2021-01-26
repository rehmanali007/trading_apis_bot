from emoji import emojize


def get_circles(liq):
    liq = int(liq)
    circles = ''
    if liq == 0:
        return circles
    green_circle = emojize(':green_circle:')
    red_circle = emojize(':red_circle:')
    if liq < 0:
        liq = -liq
        circle = red_circle
    elif liq > 0:
        circle = green_circle
    noc = int(liq / 1000)
    if noc == 0:
        return circle
    if noc > 20:
        noc = 20
    for i in range(noc):
        if i % 5 == 0:
            circles = f'{circle}\n{circles}'
            continue
        circles = f'{circle}{circles}'
    return circles


def get_fire_emojies(mentions):
    mentions = int(mentions)
    emojies = ''
    if mentions == 0:
        return emojies
    fire = emojize(':fire:')
    noc = int(mentions / 10)
    if noc == 0:
        return fire
    if noc > 20:
        noc = 20
    for i in range(noc):
        if i % 5 == 0:
            emojies = f'{fire}\n{emojies}'
            continue
        emojies = f'{fire}{emojies}'
    return emojies


if __name__ == '__main__':
    e = get_fire_emojies(2000)
    print(e)
