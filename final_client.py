import socket
import chatlib  # To use chatlib functions or consts, use chatlib.****

SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 5678

# HELPER SOCKET METHODS

def build_and_send_message(conn, code, data):
    """
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Paramaters: conn (socket object), code (str), data (str)
    Returns: Nothing
    """

    message_to_send = chatlib.build_message(code, data)
    conn.send(message_to_send.encode())


def recv_message_and_parse(conn):
    """
    Recieves a new message from given socket,
    then parses the message using chatlib.
    Paramaters: conn (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If error occured, will return None, None
    """
    full_msg = conn.recv(1024).decode()
    cmd, data = chatlib.parse_message(full_msg)
    return cmd, data

def build_send_recv_parse(conn, cmd, data):
    build_and_send_message(conn, cmd, data)
    return recv_message_and_parse(conn)

def get_score(conn):
    cmd, data = build_send_recv_parse(conn, "MY_SCORE", "")
    if cmd != "YOUR_SCORE":
        error_and_exit(data)
    else:
        print("\nYour score is: " + data)

def get_highscore(conn):
    cmd, data = build_send_recv_parse(conn, "HIGHSCORE", "")
    if cmd != "ALL_SCORE":
        error_and_exit(data)
    else:
        print("\nHigh score:\n" + data)

def play_question(conn):
    cmd, data = build_send_recv_parse(conn, "GET_QUESTION", "")
    if cmd == "NO_QUESTIONS":
        print("\nNo questions left!")
        return
    question_parts = data.split("#")
    print(f"\nQ: {question_parts[1]}\n 1: \t{question_parts[2]}\n 2: \t{question_parts[3]}\n 3: \t{question_parts[4]}\n 4: \t{question_parts[5]}")
    user_answer = int(input("Please, choose an answer [1-4]: "))
    cmd, data = build_send_recv_parse(conn, "SEND_ANSWER", f"{question_parts[0]}#{user_answer}")
    if cmd == "CORRECT_ANSWER":
        print("\nYou were right! 5 points added!!")
    else:
        print("\nYou were wrong :( answer is: #" + data)

def get_logged_users(conn):
    cmd, data = build_send_recv_parse(conn, "LOGGED", "")
    logged_users = data.replace(",", "\n")
    print("\nLogged users are:\n" + logged_users)

def connect():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
    return client_socket


def error_and_exit(error_msg):
    print(error_msg)
    exit()


def login(conn):
    while True:
        user_name = input("Please enter username: ")
        pass_word = input("Please enter password: ")
        build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"],f"{user_name}#{pass_word}")
        cmd, data = recv_message_and_parse(conn)
        if cmd == chatlib.PROTOCOL_SERVER["login_ok_msg"]:
            print("\nLogin successful!")
            break
        print(data)

def logout(conn):
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"], "")
    print("\nLogout successful!")

def main():

    client_socket = connect()
    login(client_socket)
    while True:
        user_chice = input("\nPlease pick an option: \np\t Play a trivia question\ns\t Get my score\nh\t Get high score\nl\t Get logged users\nq\t Quit\n")
        if user_chice == "q":
            logout(client_socket)
            break
        elif user_chice == "s":
            get_score(client_socket)
        elif user_chice == "h":
            get_highscore(client_socket)
        elif user_chice == "l":
            get_logged_users(client_socket)
        elif user_chice == "p":
            play_question(client_socket)
        else:
            print("\nWrong move!")

    client_socket.close()

if __name__ == '__main__':
    main()
