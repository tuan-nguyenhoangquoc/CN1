import os
import socket as sk
import shutil
import threading
import time
import tkinter as tk
import customtkinter as ctk
from tkinter import END, filedialog
from tkinter import messagebox



SIZE = 1024
REPOSITORY_PATH = 'repository/'
DOWNLOAD_PATH = 'download/'
FORMAT = 'utf-8'


def get_local_ip():
    s = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
    try:
        s.connect(('192.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


class Client:
    def __init__(self, IP, port, hostname):
        self.client_socket = None
        self.server_IP = IP
        self.server_Port = port
        self.hostname = hostname
        self.isConnected = False
        self.peer_socket = None

    
    def download_file(self, target_IP = '127.0.0.1', target_Port = 2153, fileName = ''):
        self.peer_socket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        try:
            self.peer_socket.connect((target_IP, target_Port))
        except:
            print(f'Failed to connect to peer: {target_IP}:{target_Port}')
        print(f'Connected to peer: {target_IP}:{target_Port}')

        request = 'FETCH@' + fileName
        self.peer_socket.send(request.encode(FORMAT))


        #data = self.peer_socket.recv(SIZE)
        
        filePath = os.path.join(os.getcwd(), DOWNLOAD_PATH)
        filePath += fileName
        file = open(filePath, 'wb')
        while True:
            data = self.peer_socket.recv(SIZE)
            if not data or data == 'DONE'.encode(FORMAT):
                break
            file.write(data)
            self.peer_socket.send('OK'.encode(FORMAT))
        file.close()
        print('Received ' + fileName + f' from {target_IP}')
        self.peer_socket.close()


    ##### Start send request #####
    def start_request(self):
        while self.isConnected:
            self.choosing_option()


    ##### Client choose option #####
    def choosing_option(self):

        print('Enter your command:\n> publish `lname` `fname`: Add a file named `fname` from `lname` to repository and convey to the server\n> fetch `fname`: Find some copy of the file named `fname` and add it to repository\n> quit: Disconnect from server')
        
        option = input('Your command: ')
        if option.startswith('publish'):
            lname = option.split(' ')[1]
            fname = option.split(' ')[2]
            self.publish(lname, fname)
        elif option.startswith('fetch'):
            fname = option.split(' ')[1]
            self.fetch(fname)
        elif option == 'quit':
            self.disconnect(self.client_socket, self.server_IP, self.server_Port)
            self.isConnected = False
            self.client_server.close()
            exit(0)
        else:
            print('Invalid Command')

    def quitCli(self):
        self.disconnect(self.client_socket, self.server_IP, self.server_Port)
        self.isConnected = False
        self.client_server.close()
        exit(0)
    ####### Disconnect from server ########
    def disconnect(self, my_socket = sk.socket, other_IP = '127.0.0.1', other_Port = 1502):

        msg = f'DISCONNECT@Disconnected from server {other_IP}:{other_Port}'

        my_socket.send(msg.encode(FORMAT))
        print(msg.split('@')[1])
        my_socket.close()


    ##### Publish all file in repository when connect to server #####
    def publish_all(self):

        filePath = os.path.join(os.getcwd(), REPOSITORY_PATH)
        fileList = ''
        
        for file in os.listdir(filePath):
            fileList += file + ' '
        
        if fileList != '':
            msg = 'PUBLISH@' + fileList
            self.client_socket.send(msg.encode(FORMAT))
            server_respond = self.client_socket.recv(SIZE).decode(FORMAT)
            _ = server_respond.split('@')
            print('Published all file to the server.')


    def publish(self, lname = '', fname = ''):
        filePath = os.path.join(lname, fname)
        if not os.path.exists(filePath):
            print('This file does not exist on your system.')
        else:
            shutil.copy(filePath, os.path.join(os.getcwd(), REPOSITORY_PATH))

        msg = 'PUBLISH@' + fname
        self.client_socket.send(msg.encode(FORMAT))
        
        server_respond = self.client_socket.recv(SIZE).decode(FORMAT)
        _, server_message = server_respond.split('@')
        print(server_message)
        return server_message


    def fetch(self, fname = ''):

        filePath = os.path.join(REPOSITORY_PATH, fname)
        if not os.path.exists(filePath):
            msg = 'FETCH@' + fname
            self.client_socket.send(msg.encode(FORMAT))
            
            server_respond = self.client_socket.recv(SIZE).decode(FORMAT)
            server_command, server_message = server_respond.split('@')
            if server_command == 'OK':
                clientList = []
                while True:
                    clients = self.client_socket.recv(SIZE).decode(FORMAT)
                    if clients.startswith('DONE'):
                        break
                    else:
                        clientList.append(clients)
                    self.client_socket.send('Received'.encode(FORMAT))
                if (clientList):
                    print(server_message, clientList)
                    target_IP = clientList[0].split(':')[0]
                    self.download_file(target_IP, 2153, fname)
                    return server_message
                else:
                    print('File not found on the server')
                    return server_message
            else:
                print(server_message)
                return server_message
        else:
            msg = 'ERROR@File existed in repository.'
            print(msg.split('@')[1])
            return msg.split('@')[1]


    def listening(self):
        while self.isConnected:
            self.sending_to_peers()


    def sending_to_peers(self):
        try:
            other_socket, other_address = self.client_server.accept()
            print(f"Peer {other_address} connected.")
            try:
                request = other_socket.recv(SIZE).decode(FORMAT)
            except:
                print('Waiting for request...')

            #request = other_socket.recv(SIZE).decode(FORMAT)
            fileName = request.split('@')[1]
            self.transfer_file(other_socket, other_address[0], fileName)
        except:
            if not self.isConnected:
                print('CLOSE')
                exit(0)  

        
    def transfer_file(self, receiver = sk.socket, receiver_IP = '127.0.0.1', fileName = ''):
        filePath = os.path.join(os.getcwd(), REPOSITORY_PATH)
        filePath += fileName
        file = open(filePath, 'rb')
        while True:
            data = file.read(SIZE)
            if not data:
                receiver.send('DONE'.encode(FORMAT))
                break
            receiver.send(data)
            _ = receiver.recv(SIZE).decode(FORMAT)
        file.close()
        print('Sent ' + fileName + f' to peer: {receiver_IP}')
        receiver.close()

    def deleteFile(self, fname):
        filePath = os.path.join(REPOSITORY_PATH, fname)
        os.remove(filePath)
        msg = 'DELETE@' + fname
        self.client_socket.send(msg.encode(FORMAT))

        server_respond = self.client_socket.recv(SIZE).decode(FORMAT)
        _, server_message = server_respond.split('@')
        print(server_message)
        return server_message

    def start(self):
        if not os.path.exists(REPOSITORY_PATH):
            os.makedirs(REPOSITORY_PATH)
        if not os.path.exists(DOWNLOAD_PATH):
            os.makedirs(DOWNLOAD_PATH)
        
        self.client_socket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        try:
            self.client_socket.connect((self.server_IP, self.server_Port))
        except:
            print(f"Failed to connect to server: {self.server_IP}:{self.server_Port}")
            return
        self.isConnected = True
        self.client_socket.send(self.hostname.encode(FORMAT))
        _ = self.client_socket.recv(SIZE).decode(FORMAT)
        print(f"Connected to server: {self.server_IP}:{self.server_Port}")
        self.publish_all()
        self.request_thread = threading.Thread(target=self.start_request)
        self.request_thread.start()
        time.sleep(0.2)

        self.client_server = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        self.client_server.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
        self.client_server.bind((get_local_ip(), 2153))
        self.client_server.listen()
        
        self.listen_thread = threading.Thread(target=self.listening)
        self.listen_thread.start()

class ClientGUI:
    def __init__(self):
        self.app = ctk.CTk()
        self.client =  Client('',0,'')
        self.GUIobject()

    def setup(self):
        ctk.set_appearance_mode('light')
        ctk.set_default_color_theme('green')
        self.app.title('Client')
        self.app.geometry('700x500')


    def GUIobject(self):
        self.login_Frame = ctk.CTkFrame(master=self.app,
                            width=800,
                            height=200,
                            bg_color='black')
        self.login_Frame.pack(padx=10, pady=10, expand=True, fill="both", side="left")

        self.Entry_Frame = ctk.CTkFrame(master=self.login_Frame,
                            width=250,
                            height=100,
                           )
        self.Entry_Frame.place(relx=0.5,rely=0.3,anchor=tk.CENTER)
        

        self.serverIP_Entry = ctk.CTkEntry(master=self.Entry_Frame,
                                    placeholder_text='Server IP',
                                    width=200,
                                    height=30,
                                    text_color='black',
                                    corner_radius=10)
        self.serverIP_Entry.configure(state='normal')
        self.serverIP_Entry.pack(padx=5, pady=5, expand=True, fill="none", side="top", anchor="ne")

        self.hostname_Entry = ctk.CTkEntry(master=self.Entry_Frame,
                                    placeholder_text='Hostname',
                                    width=200,
                                    height=30,
                                    text_color='black',
                                    corner_radius=10)
        self.hostname_Entry.configure(state='normal')
        self.hostname_Entry.pack(padx=5, pady=5, expand=True, fill="none", side="bottom", anchor="ne")

    
        self.connect_Button = ctk.CTkButton(master=self.app, text='Connect', command=self.start_connect)
        self.connect_Button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    

    def start_connect(self):
        if not self.serverIP_Entry.get() or not self.hostname_Entry.get():
            messagebox.showerror("Error", "Please fill in both Server IP and Hostname!")
            return
        SERVER_IP = self.serverIP_Entry.get()
        SERVER_PORT = 1502
        hostname = self.hostname_Entry.get()

        self.client = Client(SERVER_IP, SERVER_PORT, hostname)
        self.client.start()
        time.sleep(1)
        
        
        self.login_Frame.pack_forget()
        self.show_repository_frame()

    def show_repository_frame(self):
        #### MAIN FRAME
        self.repo_frame = ctk.CTkFrame(master=self.app, width=800, height=400, bg_color='black')
        self.repo_frame.pack(padx=10, pady=10, expand=True, fill="both", side="left")

        name = "Hostname: " + self.hostname_Entry.get()
        Hostname_label = tk.Label(master=self.repo_frame, text=name, fg='black',bg='gray', font=("Family", 14))
        Hostname_label.place(relx=0.04, rely=0.07)


        self.font1 = ('Arial',20,'bold')
        self.font2 = ('Arial',15,'bold')
        self.font3 = ('Arial',10,'bold')
        self.user_repo_label = ctk.CTkLabel(master=self.repo_frame,font=self.font1, text='File Sharing', text_color='black')
        self.user_repo_label.pack()

        
        #### HOST REPO FRAME
        self.Host_Repo_Frame = ctk.CTkFrame(master=self.repo_frame,
                            width=240,
                            height=400,
                            fg_color='gray'
                           )
        self.Host_Repo_Frame.pack(padx=10, pady=10, expand=True, fill="none", side="right")
        self.Host_Repo_Frame.place(x = 30,y=60)

        repo_Label = tk.Label(self.Host_Repo_Frame, text="Repository", font=("Family", 15, 'bold'), fg='black', bg='gray')
        repo_Label.place(relx=0.3, anchor='nw')

        self.repo_list = tk.Listbox(master=self.Host_Repo_Frame,width=40, height=15, font=self.font3)
        self.repo_list.pack(side="bottom", anchor="se",padx=30,pady=35)
        self.repo_list.config(bg="white",borderwidth=2, relief="groove",selectmode="BROWSE")

        path = os.getcwd()
        newpath = path + '/repository'
        repo_filename = os.listdir(newpath)
        
        for filename in repo_filename:
            self.repo_list.insert(tk.END,filename)

        #### OPTIONS FRAME
        self.options_Frame = ctk.CTkFrame(master=self.repo_frame,
                            width=240,
                            height=270,
                           )
        self.options_Frame.pack(padx=5, pady=5,  fill="none", side="top", anchor="ne")
        self.options_Frame.place(x = 350,y=60)

        self.FD_Frame = ctk.CTkFrame(master=self.options_Frame,
                            width=300,
                            height=250,
                           )
        self.FD_Frame.pack(padx=5, pady=5, expand=True, fill="none", side="top", anchor="ne")
        #### FETCH FRAME
        self.Fetch_Frame = ctk.CTkFrame(master=self.FD_Frame,
                            width=300,
                            height=100,
                            fg_color='gray'
                           )
        self.Fetch_Frame.pack(padx=5, pady=5, expand=True, fill="none", side="top", anchor="ne")
        # n, ne, e, se, s, sw, w, nw, or center
        fetch_Label = tk.Label(self.Fetch_Frame, text="Fetch file", font=("Family", 14), fg='black', bg='gray')
        fetch_Label.place(relx=0.1, rely=0.15, anchor='nw')
        self.fetch_Entry = ctk.CTkEntry(master=self.Fetch_Frame,
                                    placeholder_text='Enter filename',
                                    width=180,
                                    height=30,
                                    text_color='black',
                                    corner_radius=10)
        self.fetch_Entry.configure(state='normal')
        self.fetch_Entry.place(relx=0.35, rely=0.6, anchor=tk.CENTER)

        fetch_Button = ctk.CTkButton(master=self.Fetch_Frame,width=85, height=30, text='FETCH', command=self.fetchFile)
        fetch_Button.place(relx=0.8, rely=0.6, anchor=tk.CENTER)

        #### DISCOVER FRAME
        self.delete_Frame = ctk.CTkFrame(master=self.FD_Frame,
                            width=300,
                            height=100,
                            fg_color='gray'
                           )
        self.delete_Frame.pack(padx=5, pady=5, expand=True, fill="none", side="bottom", anchor="se")

        self.delete_Entry = ctk.CTkEntry(master=self.delete_Frame,
                                    placeholder_text='Enter filename',
                                    width=180,
                                    height=30,
                                    text_color='black',
                                    corner_radius=10)
        delete_Label = tk.Label(self.delete_Frame, text="Delete file",  font=("Arial", 14),fg='black', bg='gray')
        delete_Label.place(relx=0.1, rely=0.15, anchor='nw')
        self.delete_Entry.configure(state='normal')
        self.delete_Entry.place(relx=0.35, rely=0.6, anchor=tk.CENTER)
            
        delete_Button = ctk.CTkButton(master=self.delete_Frame,width=85, height=30, fg_color='#990000', hover_color='red',text='DELETE', command=self.deleteFile)
        delete_Button.place(relx=0.8, rely=0.6, anchor=tk.CENTER)

        #### PUBLISH BUTTON
        self.publish_button = ctk.CTkButton(master=self.repo_frame, 
                                            font=self.font2, text_color='white', 
                                            text='Publish', fg_color='#06911f', 
                                            hover_color='#06911f', 
                                            bg_color = '#09112e', 
                                            cursor= 'hand2', corner_radius=5, width=120, command=self.openFile)
        self.publish_button.place(relx=0.15, rely=0.8)

        #### DISCONNECT BUTTON
        self.quit_Button = ctk.CTkButton(master=self.repo_frame, 
                                            font=self.font2, text_color='white', 
                                            text='Disconnect', fg_color='red', 
                                            hover_color='#990000', 
                                            cursor= 'hand2', corner_radius=5, width=120, command=self.quitCli)
        self.quit_Button.place(relx=0.6, rely=0.85)


    def openFile(self): 
        filepath = filedialog.askopenfilename()
        directory, filename = os.path.split(filepath)
        print(directory)
        print(filename)
        msg = self.client.publish(directory,filename)

        if msg == "Uploaded successfully!":
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("Error", msg)
        
        self.repo_list.delete(0,END)
        path = os.getcwd()
        newpath = path + '/repository'
        repo_filename = os.listdir(newpath)
        for filename in repo_filename:
            self.repo_list.insert(tk.END,filename)
        
    def quitCli(self):
        self.app.withdraw()
        self.client.quitCli()

    def fetchFile(self):
        if not self.fetch_Entry.get():
            messagebox.showerror("Error", "Please fill in filename!")
            return
        # Create a loading indicator label
        loading_label = tk.Label(master=self.repo_frame, text='Loading...', fg='white',bg='black', font=("Arial", 14))
        loading_label.pack(padx=10, pady=10,side='bottom')

        # Start the fetch operation in a separate thread
        def fetch_thread():
            msg = self.client.fetch(self.fetch_Entry.get())
            if msg == 'These are clients having the file:':
                messagebox.showinfo("Success", "Done fetch file!")
            else:
                messagebox.showerror("Error", msg)

            # Remove the loading indicator
            loading_label.destroy()

        thread = threading.Thread(target=fetch_thread)
        thread.start()

    def deleteFile(self):
        if not self.delete_Entry.get():
            messagebox.showerror("Error", "Please fill in filename!")
            return
        msg = self.client.deleteFile(self.delete_Entry.get())
        messagebox.showinfo("Notice",msg)
        self.repo_list.delete(0,END)
        path = os.getcwd()
        newpath = path + '/repository'
        repo_filename = os.listdir(newpath)
        for filename in repo_filename:
            self.repo_list.insert(tk.END,filename)


if __name__ == '__main__':
    app = ClientGUI()
    app.setup()
    app.app.mainloop()
