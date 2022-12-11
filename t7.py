from general.keys import get_next_key, reset_key

if __name__ == '__main__':
    reset_key('BEDRIJF', 13)
    for _ in range(4):
        x = get_next_key('BEDRIJF')
        y1 = get_next_key('AANVRAGEN')
        y2 = get_next_key('AANVRAGEN')
        print(f'bedrijf: {x}  aanvraag: {y1}  {y2}')
    reset_key('AANVRAGEN', 100)
    for _ in range(4):
        x = get_next_key('BEDRIJF')
        y1 = get_next_key('AANVRAGEN')
        y2 = get_next_key('AANVRAGEN')
        print(f'bedrijf: {x}  aanvraag: {y1}  {y2}')
