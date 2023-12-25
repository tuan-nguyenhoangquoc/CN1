import tkinter as tk
from tkinter import *
from tkinter import messagebox
import customtkinter as ctk
from customtkinter import ThemeManager
import threading
import pyperclip
import socket as sk
import time


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
 
SERVER_IP = get_local_ip()
SERVER_PORT = 1502

SIZE = 1024
FORMAT = 'utf-8'

class Server:
    def __init__(self, ip, port):
        self.server = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        self.server_ip = ip
        self.server_port = port
        self.server.bind((ip, port))
        self.server.listen()
        self.onlineClient = dict()
        self.connectedClient = dict()
        self.clientFileList = dict()

    

    def start_request(self):
        while True:
            self.server_option()


    def server_option(self):
        print('\nEnter your command:\n> discover `hostname`: discover the list of local files of hostname\n> ping `hostname`: live check hostname')
        option = input('\nYour command: ')
        if option.startswith('discover'):
            print(self.discover(option.split(' ')[1]))
        elif option.startswith('ping'):
            self.ping(option.split(' ')[1])


    def handle_client(self, client_socket, client_address, client_name):
        while True:
            # Receive client's requests
            try:
                client_request = client_socket.recv(SIZE).decode(FORMAT)
            except:
                print('Waiting for a request...')

            client_command, client_message = client_request.split('@')         # Client request in format `cmd@msg`
            
            if client_command != 'DISCONNECT':
                print(f"\n[{client_address}]Client's request: [{client_command}]", client_message)

            if client_command == 'PUBLISH':
                fileName = client_message.split(' ')
                if client_address in self.clientFileList:
                    fileName = fileName[0]
                    if (fileName not in self.clientFileList[client_address]):
                        self.clientFileList[client_address].append(fileName)
                        cmd = 'OK'
                        msg = 'Uploaded successfully!'
                    else:
                        cmd = 'ERROR'
                        msg = 'FileName existed in repository'
                else: #client_address chua co trong filelist
                    self.clientFileList[client_address] = fileName[:-1]
                    cmd = 'OK'
                    msg = 'Uploaded successfully!'
                
                self.send_message(client_socket, cmd, msg)
                print(msg)
                
            elif client_command == 'FETCH':
                fileName = client_message
                curClientList = list()
                for cli in self.clientFileList:
                    if fileName in self.clientFileList[cli] and cli in self.onlineClient.values():
                        curClientList.append(cli)
                if curClientList:
                    self.send_message(client_socket, 'OK', 'These are clients having the file:')
                    for client in curClientList:
                        client = client[0] + ':' + str(client[1])
                        client_socket.send(client.encode(FORMAT))
                        _ = client_socket.recv(SIZE).decode(FORMAT)
                    
                    self.send_message(client_socket, 'DONE', 'All clients are sent.')
                    self.clientFileList[client_address].append(fileName)
                    print(f'All clients are sent to [{client_address}]')
                else:
                    self.send_message(client_socket, 'ERROR', 'Filename does not exist on server.')
                    print('Filename does not exist.')

            elif client_command == 'ERROR':
                print(client_message)
            elif client_command == 'DELETE':
                fileName = client_message
                self.clientFileList[client_address].remove(fileName)
                self.send_message(client_socket, 'DONE', 'Deleted file')

            else:
                print(f'Client {client_address} disconnected.')
                self.onlineClient.pop(client_name)
                client_socket.close()
                break
    
    def send_message(self, client_socket, cmd, msg):
        respond = cmd + '@' + msg
        client_socket.send(respond.encode(FORMAT))

    def ping(self, hostname = ''):
        if hostname not in self.connectedClient:
            output = 'This host have not connected to server yet.'
        else:
            if hostname in self.onlineClient:
                output = 'Online'
            else:
                output = 'Offline'

        print(output)
        return output


    def discover(self, hostname = ''):
        if hostname in self.connectedClient:
            return self.clientFileList[self.connectedClient[hostname]]
        else:
            return hostname + " have not connected to server yet."

    def start(self):
        print(f"Server is listening on {self.server_ip}")
        while True:
            threading.Thread(target=self.start_request).start()
            
            client_socket, client_address = self.server.accept()
            client_name = client_socket.recv(SIZE).decode(FORMAT)
            print('\nClient ' + client_name + f' (IP Address: {client_address}) connected.')
            self.connectedClient[client_name] = client_address
            client_socket.send('_'.encode(FORMAT))
            self.onlineClient[client_name] = client_address

            threading.Thread(target=self.handle_client, args=(client_socket, client_address, client_name)).start()
            time.sleep(1)
            

class ServerUI:
    def __init__(self):
        self.app = ctk.CTk()
        # super().__init__()
        self.server = Server(SERVER_IP, SERVER_PORT)
        svip = SERVER_IP
        pyperclip.copy(svip)
        self.UIObject()
        self.main_Frame.pack_forget()

    def setup(self):
        ctk.set_appearance_mode('dark')
        ctk.set_default_color_theme('green')
        self.app.title('Server')
        self.app.geometry('800x600')
        
    def run_server(self):
        self.server.start()

    def start_connect(self):
        self.login_Frame.pack_forget()
        self.main_Frame.pack(padx=15, pady=15, expand=True, fill='both', side='right')
        server_thread = threading.Thread(target=self.run_server)
        server_thread.start()
        

    def UIObject(self):
        #### LOGIN FRAME
        self.login_Frame = ctk.CTkFrame(master=self.app,
                            width=800,
                            height=200,
                           )
        self.login_Frame.pack(padx=15, pady=15, expand=True, fill="both", side="top")
        button_font = ('Arial',20,'bold')
        self.connect_Button = ctk.CTkButton(master=self.login_Frame, font = button_font,text='START SERVER', command=self.start_connect)
        # self.connect_Button.place(relx=0.5, rely=0.7, anchor=tk.CENTER)
        self.connect_Button.pack(padx=10, pady=230)
        self.font3 = ('Arial',10,'bold')

        #### MAIN FRAME

        #### Server listing
        self.main_Frame = ctk.CTkFrame(master=self.app,
                                width=800,
                                height=600,
                                )
        self.main_Frame.pack(padx=10, pady=10, expand=True, fill='none', side='left')
        server_ip_text = "Server is listening on " + str(self.server.server_ip) # + ":" + str(self.server.server_port)
        main_Label = tk.Label(self.main_Frame, text=server_ip_text, font=("Arial", 13, 'bold'), fg='white', bg='gray')
        main_Label.place(anchor='nw', x=400, y=10)


        #### CONNECTED FRAME
        self.connected_Frame = ctk.CTkFrame(master=self.main_Frame,
                            width=300,
                            height=300,
                            fg_color='blue'
                           )
        self.connected_Frame.pack(padx=50, pady=60, expand=True, fill="none", side="right")

        repo_Label = tk.Label(self.connected_Frame, text="Hostname List", font=("Family", 15, 'bold'), fg='black', bg='gray')
        repo_Label.place(relx=0.3, anchor='nw')

        self.connected_list = tk.Listbox(master=self.connected_Frame,width=40, height=15, font=self.font3)
        self.connected_list.pack(side="bottom", anchor="se",padx=30,pady=35)
        self.connected_list.config(bg="white",borderwidth=2, relief="groove",selectmode="BROWSE")

        self.connect_Button = ctk.CTkButton(master=self.connected_Frame,width=30, height=16,text='F5', command=self.F5_display_connectedList)
        self.connect_Button.place(relx=0.5, rely=0.985, anchor='s')

        #### OPTIONS FRAME WHICH INCLUDES PING FRAME AND DISCOVER FRAME
        self.options_Frame = ctk.CTkFrame(master=self.main_Frame,
                            width=300,
                            height=250,
                           )
        self.options_Frame.pack(padx=5, pady=5, expand=True, fill="none", side="top", anchor="ne")
        #### PING FRAME
        self.ping_Frame = ctk.CTkFrame(master=self.options_Frame,
                            width=300,
                            height=100,
                            fg_color='blue'
                           )
        self.ping_Frame.pack(padx=5, pady=5, expand=True, fill="none", side="top", anchor="ne")
        # n, ne, e, se, s, sw, w, nw, or center
        pingHostname_Label = tk.Label(self.ping_Frame, text="Ping Hostname", font=("Family", 14), fg='black', bg='gray')
        pingHostname_Label.place(relx=0.1, rely=0.15, anchor='nw')
        self.pingHostname_Entry = ctk.CTkEntry(master=self.ping_Frame,
                                    placeholder_text='Enter Hostname',
                                    width=180,
                                    height=30,
                                    text_color='black',
                                    corner_radius=10)
        self.pingHostname_Entry.configure(state='normal')
        self.pingHostname_Entry.place(relx=0.35, rely=0.6, anchor=tk.CENTER)

        pingHostname_Button = ctk.CTkButton(master=self.ping_Frame,width=85, height=30, text='PING', command=self.ping_hostname)
        pingHostname_Button.place(relx=0.8, rely=0.6, anchor=tk.CENTER)

        #### DISCOVER FRAME
        self.discover_Frame = ctk.CTkFrame(master=self.options_Frame,
                            width=300,
                            height=100,
                            fg_color='blue'
                           )
        self.discover_Frame.pack(padx=5, pady=5, expand=True, fill="none", side="bottom", anchor="se")

        self.discoverHostname_Entry = ctk.CTkEntry(master=self.discover_Frame,
                                    placeholder_text='Enter Hostname',
                                    width=180,
                                    height=30,
                                    text_color='black',
                                    corner_radius=10)
        discoverHostname_Label = tk.Label(self.discover_Frame, text="Discover Hostname",  font=("Arial", 14),fg='black', bg='gray')
        discoverHostname_Label.place(relx=0.1, rely=0.15, anchor='nw')
        self.discoverHostname_Entry.configure(state='normal')
        self.discoverHostname_Entry.place(relx=0.35, rely=0.6, anchor=tk.CENTER)
            
        discoverHostname_Button = ctk.CTkButton(master=self.discover_Frame,width=85, height=30, text='DISCOVER', command=self.discover_hostname)
        discoverHostname_Button.place(relx=0.8, rely=0.6, anchor=tk.CENTER)


        #### REPO FRAME
        self.repo_Frame = ctk.CTkFrame(master=self.main_Frame,
                            width=300,
                            height=400,
                            fg_color='blue'
                           )
        self.repo_Frame.pack(padx=5, pady=5, expand=True, fill="none", side="bottom", anchor="se")

        repo_Label = tk.Label(self.repo_Frame, text="Repository", font=("Family", 14), fg='black', bg='gray')
        repo_Label.place(relx=0.38, anchor='nw')

        self.repo_list = tk.Listbox(master=self.repo_Frame,width=40, height=15, font=self.font3)
        self.repo_list.pack(side="bottom", anchor="se",padx=50,pady=30)
        self.repo_list.config(bg="white",borderwidth=2, relief="groove",selectmode="BROWSE")

    def ping_hostname(self):
        hostname = self.pingHostname_Entry.get()
        if not hostname:
            # Handle empty fields
            messagebox.showinfo("Error", "Please enter hostname!")
            return
        messagebox.showinfo("Success", self.server.ping(hostname))


    def display_repo(self, hostname=''):
        self.repo_list.delete(0,END)
        if hostname in self.server.connectedClient:
            for filename in self.server.clientFileList[self.server.connectedClient[hostname]]:
                self.repo_list.insert(tk.END,filename)

    def discover_hostname(self):
        hostname = self.discoverHostname_Entry.get()
        if not hostname:
            # Handle empty fields
            messagebox.showinfo("Error", "Please enter hostname!")
            return
        self.server.discover(hostname)
        self.display_repo(hostname)
        
    def F5_display_connectedList(self):
        self.connected_list.delete(0,END)
        for hostname in self.server.connectedClient:
            self.connected_list.insert(tk.END, hostname)
    

if __name__ == '__main__':
    app = ServerUI()
    app.setup()
    app.app.mainloop()
    
    