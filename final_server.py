import socket
import chatlib
import random
import select

# GLOBALS
users = {
	"test"	:	{"password" :"test" ,"score" :0 ,"questions_asked" :[]},
	"yossi"		:	{"password" :"123" ,"score" :50 ,"questions_asked" :[]},
	"master"	:	{"password" :"master" ,"score" :200 ,"questions_asked" :[]}
}
questions = {}
logged_users = {} # a dictionary of client hostnames to usernames - will be used later
messages_to_send = []
client_sockets = []

ERROR_MSG = "Error!"
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"


# HELPER SOCKET METHODS

def build_and_send_message(conn, code, msg):
	"""
	Builds a new message using chatlib, wanted code and message.
	Prints debug info, then sends it to the given socket.
	Paramaters: conn (socket object), code (str), msg (str)
	Returns: Nothing
	"""
	global messages_to_send

	full_msg = chatlib.build_message(code, msg)
	messages_to_send.append((conn, full_msg))

def print_client_sockets(conn_list):
	string = "\n".join([socket.getpeername() for socket in conn_list])
	print(string)

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

	print(f"{conn.getpeername()} [CLIENT]: ",full_msg)	  # Debug print
	return cmd, data
	

# Data Loaders #

def load_questions():
	"""
	Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
	Recieves: -
	Returns: questions dictionary
	"""
	questions = {
				2313 : {"question":"How much is 2+2","answers":["3","4","2","1"],"correct":2},
				4122 : {"question":"What is the capital of France?","answers":["Lion","Marseille","Paris","Montpellier"],"correct":3} 
				}
	
	return questions

# def load_user_database():
# 	"""
# 	Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
# 	Recieves: -
# 	Returns: user dictionary
# 	"""
# 	users = {
# 			"test"		:	{"password":"test","score":0,"questions_asked":[]},
# 			"yossi"		:	{"password":"123","score":50,"questions_asked":[]},
# 			"master"	:	{"password":"master","score":200,"questions_asked":[]}
# 			}
# 	return users

def create_random_question():
	questions = load_questions()
	key, value = random.choice(list(questions.items()))
	answers = "#".join(value['answers'])
	return f"{key}#{value['question']}?#{answers}"


# SOCKET CREATOR

def setup_socket():
	"""
	Creates new listening socket and returns it
	Recieves: -
	Returns: the socket object
	"""
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.bind((SERVER_IP, SERVER_PORT))
	server_socket.listen()
	return server_socket
	


		
def send_error(conn, error_msg):
	"""
	Send error message with given message
	Recieves: socket, message error string from called function
	Returns: None
	"""
	build_and_send_message(conn, "ERROR", error_msg)


##### MESSAGE HANDLING

def handle_getscore_message(conn, username):
	global users

	user_score = users[username]["score"]
	build_and_send_message(conn,"YOUR_SCORE", str(user_score))


def handle_question_message(conn):

	rand_question = create_random_question()
	build_and_send_message(conn, "YOUR_QUESTION", rand_question)


def handle_answer_message(conn, username, data):
	global users

	questions = load_questions()
	id, answer = data.split("#")
	if questions[int(id)]["correct"] ==  int(answer):
		build_and_send_message(conn, "CORRECT_ANSWER", "")
		users[username]["score"] += 5
	else:
		right_answer = f"{questions[int(id)]['correct']}"
		build_and_send_message(conn, "WRONG_ANSWER", right_answer)

def handle_highscore_message(conn):
	global users

	my_list = []
	for user in users:
		my_list.append((user, users[user]["score"]))
	my_list.sort(key = lambda s: -s[1])

	send_to_client = ""
	for user, score in my_list:
		send_to_client += f"{user}: {score}\n"

	build_and_send_message(conn, "ALL_SCORE",send_to_client)


def handle_logged_message(conn):
	global users
	global logged_users

	# THIS is how logged_users dic look like -->   user_address: "username"
	send_to_client = ",".join([user for user in logged_users.values()])
	build_and_send_message(conn, "LOGGED_ANSWER",send_to_client)

def handle_logout_message(conn):
	"""
	Closes the given socket (in laster chapters, also remove user from logged_users dictioary)
	Recieves: socket
	Returns: None
	"""
	global logged_users
	global client_sockets

	del logged_users[conn.getpeername()]
	client_sockets.remove(conn)
	print("Client logged off!", conn.getpeername())
	conn.close()


def handle_login_message(conn, data):
	"""
	Gets socket and message data of login message. Checks  user and pass exists and match.
	If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
	Recieves: socket, message code and data
	Returns: None (sends answer to client)
	"""
	global users  # This is needed to access the same users dictionary from all functions
	global logged_users	 # To be used later

	user_password = chatlib.split_data(data, 1)
	if user_password == [None]:
		send_error(conn, "There isn't 2 field separated by 1 delimiter")
	else:
		user_name = user_password[0]
		password = user_password[1]
		if user_name in users:
			if users[user_name]["password"] == password:
				build_and_send_message(conn, "LOGIN_OK", "")
				logged_users[conn.getpeername()] = user_name
			else:
				send_error(conn, f"{ERROR_MSG} Password does not match!")
		else:
			send_error(conn, f"{ERROR_MSG} Username does not exist")


def handle_client_message(conn, cmd, data):
	"""
	Gets message code and data and calls the right function to handle command
	Recieves: socket, message code and data
	Returns: None
	"""
	global logged_users	 # To be used later

	if conn.getpeername() not in logged_users:
		if cmd == "LOGIN":
			handle_login_message(conn, data)
		else:
			send_error(conn, "Must login first!")
	else:
		if cmd == "LOGOUT":
			handle_logout_message(conn)
		elif cmd == "MY_SCORE":
			handle_getscore_message(conn, logged_users[conn.getpeername()])
		elif cmd == "HIGHSCORE":
			handle_highscore_message(conn)
		elif cmd == "LOGGED":
			handle_logged_message(conn)
		elif cmd == "GET_QUESTION":
			handle_question_message(conn)
		elif cmd == "SEND_ANSWER":
			handle_answer_message(conn, logged_users[conn.getpeername()], data)
		elif (cmd, data) == (None, None):
			conn.close()
		else:
			send_error(conn, "Unknown command!")
	


def main():
	# Initializes global users and questions dicionaries using load functions, will be used later
	global users
	global questions
	global logged_users
	global messages_to_send
	global client_sockets

	print("Welcome to Trivia Server!")

	server_socket = setup_socket()

	print("Server is up and running...")

	while True:

		try:
			ready_to_read, ready_to_write, in_error = select.select([server_socket] + client_sockets, client_sockets, [])
		except ValueError:
			for sock in client_sockets:
				if sock.fileno() == -1:
					handle_logout_message(sock)

		for current_socket in ready_to_read:
			if current_socket is server_socket:
				(client_socket, client_address) = server_socket.accept()
				print("New client joined!", client_address, "\n")
				client_sockets.append(client_socket)
			else:
				try:
					cmd, data = recv_message_and_parse(current_socket)
				except OSError:
					del logged_users[current_socket.getpeername()]
					client_sockets.remove(current_socket)
					print("Client logged off!", current_socket.getpeername())
					current_socket.close()
					break
				if cmd == "LOGOUT":
					handle_logout_message(current_socket)
					break
				else:
					handle_client_message(current_socket, cmd, data)

		for message in messages_to_send:
			if message[0] in ready_to_write:
				message[0].send(message[1].encode())
				print("[SERVER] sent: ",message[1], "\n")	  # Debug print
				messages_to_send.remove(message)


if __name__ == '__main__':
	main()

	
