import requests
from bs4 import BeautifulSoup

def get_moves_from_chesscom(game_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    response = requests.get(game_url, headers=headers)

    if response.status_code != 200:
        raise Exception("Failed to fetch the game page. Check the URL and try again.")

    soup = BeautifulSoup(response.content, 'html.parser')
    moves_div = soup.find('div', {'class': 'moveList'})
    move_list = moves_div.find_all('div', {'class': 'move'})

    moves = []

    for move in move_list:
        move_text = move.get_text(strip=True)
        moves.append(move_text)

    return moves

if __name__ == "__main__":
    # Replace this URL with the URL of the Chess.com game you want to scrape
    game_url = "https://www.chess.com/live/game/1234567890"

    try:
        moves = get_moves_from_chesscom(game_url)
        print("Moves:")
        for i, move in enumerate(moves, 1):
            print(f"{i}. {move}")
    except Exception as e:
        print("Error:", e)