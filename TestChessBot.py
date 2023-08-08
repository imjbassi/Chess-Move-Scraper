from lib2to3.pgen2 import driver
import os
import re
import time
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import chess
import chess.engine
import chess.pgn
from configparser import ConfigParser

# There are 3 mode options: bullet, blitz, rapid.
# Bullet for fast-paced 1-minute games,
# Blitz for 3-5 minute games, rapid for 10-minute games.
mode = 'blitz'
user = ''
# File locations
file_location = os.path.abspath(__file__)
# engine_location = "/Users/jaiveerbassi/Downloads/stockfish/stockfish-ubuntu-x86-64-avx2"
engine_location = "/opt/homebrew/Cellar/stockfish/16/bin/stockfish"
stockfish_location = file_location[:-9] + engine_location
account_location = file_location[:-8] + "/Users/jaiveerbassi/Downloads/account.txt"
total_search_opponents = 0
if_won_message = ""

# Account credentials
def Credentials():
    global user
    with open(account_location, "r") as f:
        user = f.readline().strip()
        password = f.readline().strip()
    if not user and not password:
        print("Username/password not found in akun.txt")
        user = input("username: ")
        password = input("password: ")
    return [user, password]

# Open selenium
def open_selenium():
    options = webdriver.FirefoxOptions()
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0")
    driver = webdriver.Firefox(options=options)
    driver.get("https://www.chess.com/login")
    return driver

# Login
def login(driver, user, password):
    form_user = driver.find_element_by_id("username")
    form_user.send_keys(user)
    form_password = driver.find_element_by_id("password")
    form_password.send_keys(password)
    form_password.send_keys(Keys.RETURN)
    time.sleep(5)
    driver.get("https://www.chess.com/live")

# Create notation / pgn
def create_notation():
    notation_location = file_location[:-8] + "history/pgn.pgn"
    open(notation_location, "w+").close()
    return notation_location

# Detect move step
def detect_move(driver, move_num):
    colors = [1, 0]
    next_move = ""
    color = colors[move_num % 2]
    location = (move_num + 1) // 2
    xpath = f"/html/body/div[3]/div/div[1]/div[1]/div/div[1]/div/div/div[{location}]/span[{color+2}]/span[contains(@class, 'vertical-move-list-clickable')]"
    WebDriverWait(driver, 120).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )
    move_element = driver.find_element_by_xpath(xpath)
    print(move_num, move_element.text)

    if move_element.text[0].isdigit():
        print("GAME OVER")
        driver.get("https://www.chess.com/live")
        return
    if move_num % 2 == 1:
        return str(location) + "." + move_element.text + " "
    else:
        return move_element.text + " "

# Find the best move
def find_best_move(engine, notation, depth):
    with open(notation, "r") as f:
        game = chess.pgn.read_game(f)
        board = chess.Board()
        for move in game.mainline_moves():
            board.push(move)
        best_move = engine.play(board, chess.engine.Limit(depth=depth)).move
        return best_move

# Skip aborted game
def skip_aborted():
    try:
        game_over = driver.find_element_by_class_name("game-over-dialog-content")
        if game_over:
            try:
                time.sleep(5)
                new_game = driver.find_element_by_class_name("game-over-button-button").click()
                print("Skip aborted game")
                time.sleep(1)
                driver.get("https://www.chess.com/live")
            except:
                pass
    except:
        pass

    try:
        opponent_won = driver.find_element_by_class_name("game-over-header-userWon")
        if opponent_won:
            try:
                time.sleep(5)
                new_game = driver.find_element_by_class_name("game-over-button-button").click()
                print("Skip game because the opponent won")
                time.sleep(1)
                driver.get("https://www.chess.com/live")
            except:
                pass
    except:
        pass

# Select promoted pawn that goes to school
def choose_promotion(driver, best_move):
    # To use this feature, please email: tinwaninja@gmail.com
    eligible_promotions = ['tinwaninja@gmail.com']
    try:
        if any(str(best_move) in item for item in eligible_promotions):
            print("Promotion found ", best_move)
    except:
        pass
# Suggest square
def suggest_square(driver, start_square, target_square):
    start_element = driver.find_element(By.XPATH, f'//*[@data-square="{start_square}"]')
    target_element = driver.find_element(By.XPATH, f'//*[@data-square="{target_square}"]')
    ActionChains(driver).move_to_element_with_offset(start_element, 0, 2).click().perform()
    time.sleep(0.05)
    ActionChains(driver).move_to_element_with_offset(target_element, 0, 2).click().perform()


# Main game
def main_game(driver, engine, auto_start, depth, color):
    global mode, if_won_message
    notation = create_notation()
    time.sleep(1)
    try:
        if "win 0" not in if_won_message:
            if color == 'white':
                suggest_square(driver, 'e2', 'e4')

        for move_num in range(1, 500):
            skip_aborted()
            if move_num == 1 or move_num == 2:
                if "win 0" in if_won_message:
                    print("Opponent is too weak, trying to abort match with a 25-second delay")
                    if_won_message = ""
                    time.sleep(25)
                    return
            next_move = detect_move(driver, move_num)
            with open(notation, "a") as f:
                f.write(next_move)
            best_move = find_best_move(engine, notation, depth)
            if ((color == 'white' and move_num % 2 == 0) or (color == 'black' and move_num % 2 == 1)):
                if mode == 'bullet':
                    if move_num <= 15:
                        time_delay = random.uniform(0.05, 0.10)
                        print('delay', time_delay, ' seconds')
                        time.sleep(time_delay)
                    if move_num >= 15:
                        time_delay = random.uniform(0.05, 0.25)
                        print('delay', time_delay, ' seconds')
                        time.sleep(time_delay)
                if mode == 'blitz':
                    if move_num <= 15:
                        time_delay = random.uniform(0.05, 0.25)
                        print('delay', time_delay, ' seconds')
                        time.sleep(time_delay)
                    if move_num >= 15:
                        time_delay = random.uniform(0.05, 1.25)
                        print('delay', time_delay, ' seconds')
                        time.sleep(time_delay)
                if mode == 'rapid':
                    if move_num <= 15:
                        time_delay = random.uniform(0.05, 1.25)
                        print('delay', time_delay, ' seconds')
                        time.sleep(time_delay)
                    if move_num >= 15:
                        time_delay = random.uniform(0.05, 2.25)
                        print('delay', time_delay, ' seconds')
                        time.sleep(time_delay)
                suggest_square(driver, best_move[:2], best_move[2:])
                choose_promotion(driver, best_move)

    except Exception as e:
        print("Exception occurred:", str(e))
        return

# Find color
def find_color(driver, auto_start):
    global total_search_opponents, if_won_message
    while (1):
        try:
            if auto_start:
                try:
                    check = driver.find_element_by_class_name("game-over-dialog-content")
                    print("Checking if the game has ended")
                    if check:
                        try:
                            seeking = driver.find_element_by_class_name("game-over-button-seeking")
                            print("Waiting for opponent")
                        except:
                            time.sleep(2)
                            try:
                                rematch = driver.find_element_by_xpath("/html/body/div[2]/div[2]/div[4]/div[2]/div/div[4]/button[2]").text
                                if rematch != 'Rematch':
                                    previous_won_message = driver.find_element_by_xpath("/html/body/div[2]/div[2]/div[4]/div[2]/div/div[1]/h3").text
                                    if "You Won" in previous_won_message:
                                        if "win 0" not in if_won_message:
                                            # Accept rematch with an equally skilled player
                                            rematch = driver.find_element_by_xpath("/html/body/div[2]/div[2]/div[4]/div[2]/div/div[4]/button[2]").click()
                                            print("Accept rematch with an equally skilled player")
                                        else:
                                            # Reject rematch with a weak player
                                            rematch = driver.find_element_by_xpath("/html/body/div[2]/div[2]/div[4]/div[2]/div/div[4]/button[1]").click()
                                            print("Reject rematch with a weak player")
                                    else:
                                        rematch = driver.find_element_by_xpath("/html/body/div[2]/div[2]/div[4]/div[2]/div/div[4]/button[1]").click()
                                        print("Reject rematch because the opponent is too strong")
                            except:
                                time.sleep(2)
                                new_game = driver.find_element_by_xpath("/html/body/div[2]/div[2]/div[4]/div[2]/div/div[4]/button[1]").click()
                                if new_game:
                                    print("Trying to find a new game")
                            try:
                                new_game = driver.find_element_by_class_name("game-over-button-button").click()
                                print("Trying to find a new game")
                            except:
                                try:
                                    time.sleep(1)
                                    driver.find_element_by_xpath("//li[@data-tab='challenge']").click()
                                    driver.find_element_by_class_name("quick-challenge-play").click()
                                except:
                                    pass
                except:
                    try:
                        check = driver.find_element_by_class_name("quick-challenge-play").click()
                        print("Creating a new game challenge")
                    except:
                        pass
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'draw-button-component')))
            break
        except TimeoutException:
            print("Waiting for the game to start", total_search_opponents)
            total_search_opponents += 1
            if(total_search_opponents > 8):
                total_search_opponents = 0
                try:
                    new_game = driver.find_element_by_xpath("/html/body/div[2]/div[2]/div[4]/div[2]/div/div[4]/button[1]").click()
                    if new_game:
                        print("Trying to find a new game")
                except:
                    pass
                driver.get("https://www.chess.com/live")

    components = driver.find_elements_by_class_name("chat-message-component")
    try:
        if('warn-message-component' in components[-1].get_attribute('class')):
            color_message = components[-2]
        else:
            color_message = components[-1]
        if_won_message = color_message.text
        print(color_message.text)
    except:
        return
    color_user = re.findall(r'(\w+)\s\(\d+\)', color_message.text)

    check_white = color_user[0]

    global user
    global mode
    print('Game speed mode: ' + mode)
    if check_white == user:
        print(user + ' plays as white')
        return "white"
    else:
        print(user + ' plays as black')
        return "black"

# Suggest square
def suggest_square(driver, start_square, target_square):
    start_element = driver.find_element(By.XPATH, f'//*[@data-square="{start_square}"]')
    target_element = driver.find_element(By.XPATH, f'//*[@data-square="{target_square}"]')
    ActionChains(driver).move_to_element_with_offset(start_element, 0, 2).click().perform()
    time.sleep(0.05)
    ActionChains(driver).move_to_element_with_offset(target_element, 0, 2).click().perform()


# Set settings
def set_settings():
    settings = ConfigParser()
    settings['DEFAULT'] = {'depth': '7',
                           'autoStart': '0'}
    with open('config.ini', 'w') as f:
        settings.write(f)

# Open settings
def open_settings():
    settings = ConfigParser()
    settings.read('config.ini')
    depth = int(settings['DEFAULT']['depth'])
    auto_start = int(settings['DEFAULT']['autoStart'])
    return depth, auto_start

# Main function
def main():
    driver = open_selenium()
    user, password = Credentials()
    login(driver, user, password)
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_location)
    play_again = 1
    depth, auto_start = open_settings()
    while play_again:
        skip_aborted()
        color = find_color(driver, auto_start)
        main_game(driver, engine, auto_start, depth, color)
        if auto_start:
            play_again = 1
        else:
            input_val = input("Type 'start' to continue suggesting (when the game has started), or type 'no' to quit: ")
            if input_val == 'no':
                play_again = 0
    driver.close()
    engine.close()

if __name__ == "__main__":
    main()