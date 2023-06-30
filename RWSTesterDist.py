import customtkinter as tk
import requests
import json
from bs4 import BeautifulSoup
from requests.auth import HTTPDigestAuth
from time import sleep
import websocket
import threading
import ssl
import time

class httpReq:
    """
    This class demonstrate the asked fore examples. Feel free to play around with the methods and make sure you understand whats going on.\n
    This is in no way a complete class that is ready for production, no consideration to error handling and so on has been made, see this as minimal examples.\n
    Along with this class there shoould be an example script for each task you wanted examples for. 
    """
    apiGen= None
    headers = None
    response = None
    cookies = None
    lastResponse = None
    url = None
    subNum = 0
    respType = "json"
    RWSVersion = 1
    
    

    def __init__(self, url, version = 1, userName = 'Default User', passWord = 'robotics'):
        """
        on initiatied tihs will create a session with the controller and sort the authentication.\n
        parameters:\n
            url = web server url\n
            userName = user name, defaults to Default User\n
            passWord = pass word, defaults to robotics\n
            jsonResp = if json responses are wanted set this argument to True, defaults to False\n

        """
        self.RWSVersion = version

        self.session = requests.session()
        
        self.url = url
        if version == 1:    
            self.headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                }
            self.session.auth=HTTPDigestAuth(userName, passWord)
            self.response = self.session.get(self.url, headers=self.headers, timeout = 15)        #prints result of the create que request
        
        elif version == 2:
            self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded;v=2.0',
            'Accept' : 'application/xhtml+xml;v=2.0'
            }
            self.response = self.session.get(self.url, headers=self.headers, auth=(userName, passWord), timeout = 15, verify = False) 
          
        else:
            return "wrong version"

        self.cookies = self.response.cookies.get_dict()
        self.cookie_string = '-http-session-={0}; ABBCX={1}'.format(self.cookies['-http-session-'], self.cookies['ABBCX'])
        self.lastResponse = self.response.status_code


    def urlBuilder(self, uri : str, params = {}, respType = respType):
        
        url = f"{self.url}{uri}"
        paramLen = params.__len__()
        if paramLen > 0:
            url += "?"
            i = 0
            for param in params:
                i+=1
                url += param+"="+params[param]
                if paramLen != i:
                    url += "&"
        if respType == "json" and self.RWSVersion != 2:
            if paramLen > 0:
                url += "&json=1"
            else:
                url += "?json=1"

        elif respType == "json" and self.RWSVersion == 2:
            self.headers.update({
                'Accept': 'application/hal+json;v=2.0'
            })
            
        elif respType == "XML" and self.RWSVersion == 2:
            self.headers.update({
                'Accept' : 'application/xhtml+xml;v=2.0'
            })
        return url
        

   
    def rws_get(self,url):
        self.response = self.session.get(url=url,headers = self.headers, timeout = 15, verify = False)
        return self.response
    
    def rws_post(self,url,data):
        self.response = self.session.post(url=url,headers = self.headers, data = data,timeout = 15, verify= False, stream=True)
        return self.response
    
    def rws_delete(self,url,data):
        self.response = self.session.delete(url=url,headers = self.headers, data = data,timeout = 15, verify= False)
        return self.response
    
    def rws_put(self,url,data):
        self.response = self.session.put(url=url,headers = self.headers, data = data,timeout = 15, verify= False, stream=True)
        return self.response
        

class RWSSocket:

    def on_message(self, ws, message):
        print("new message")
        soup = BeautifulSoup(message, 'html.parser')
        print(soup.prettify())

    def on_error(self, ws, error):
        print("new error ", error)

    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ### ", close_status_code)
        print("close message ",close_msg )
        print("join threads")
        self.thr.join()

    def on_open(self, ws):
        print("Opened connection")



    def __init__(self, cookie_string, wsURL, subProt):
        self.ws = websocket.WebSocketApp(url = wsURL,
                                    #on_open=self.on_open,
                                    on_message=self.on_message,
                                    #on_error=self.on_error,
                                    on_close=self.on_close,
                                    cookie = cookie_string,
                                    subprotocols=[subProt]
                                    )


    def connectThr(self):
        try:
            self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})  # Set dispatcher to automatic reconnection
        except ValueError:
            #should probably return something to main thread
            print("value error")
    
    def killSock(self):
        self.ws.close()
        

    def connectSock(self):
        self.thr = threading.Thread(target=self.connectThr)
        self.thr.start()


class test_rws:
    param_value_fields = []
    param_key_fields = []
    param_values = []
    param_keys = []
    data_value_fields = []
    data_key_fields = []
    data_values = []
    data_keys = []
    session = None
    param_row = 0

    def getCtrlinfo(self, req_type):
        #clean the output
        self.textBox.delete('1.0',tk.END)

        #this is here to later on be used to be able to reuse sessions
        if self.session == None and self.switch_var.get() == "RWS 1.0":
            try:
                self.httpReqObj = httpReq(f"http://{self.ip_addr.get()}:{self.port_number.get()}",1)  
                self.session = self.httpReqObj.session
            except requests.exceptions.ConnectionError as e:
                self.textBox.insert(tk.END, e)
                return
            except requests.exceptions.ReadTimeout as e:
                self.textBox.insert(tk.END, e)
                return
        elif  self.session == None and self.switch_var.get() == "RWS 2.0":
            try:
                self.httpReqObj = httpReq(f"https://{self.ip_addr.get()}:{self.port_number.get()}",2, userName = "Admin", passWord = "robotics")  
                self.session = self.httpReqObj.session
            except requests.exceptions.ConnectionError as e:
                self.textBox.insert(tk.END, e)
                return
            except requests.exceptions.ReadTimeout as e:
                self.textBox.insert(tk.END, e)
                return
        
        

        #add url parameters
        params ={}
        for i in range(0,self.param_values.__len__()):
            if self.param_keys[i].get() !="" and self.param_values[i].get() !="":
                params.update({self.param_keys[i].get(): self.param_values[i].get()})
        
        #add data (aka body aka payload)
        data = {}
        for i in range(0,self.data_values.__len__()):
            if self.data_keys[i].get() != "" and self.data_values[i].get() != "":
                data.update({self.data_keys[i].get(): self.data_values[i].get()})
        url = self.httpReqObj.urlBuilder(self.text.get(),params,self.switch_type.get())
        
        #make the request
        try: 
            if req_type == "get":
                response = self.httpReqObj.rws_get(url)
            elif req_type == "post":
                response = self.httpReqObj.rws_post(url,data)
            elif req_type == "put":
                response = self.httpReqObj.rws_put(url,data)
            elif req_type == "delete":
                response = self.httpReqObj.rws_delete(url,data)
                
            #print the output
            #response.status_code != 204 and response.status_code != 404 and 
           
            try:
                if self.switch_type.get() == "json":    
                    self.textBox.insert(tk.END, json.dumps(response.json(), indent = 4))
                else:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    output = str(response.status_code) + "\n" + soup.prettify()
                    self.textBox.insert(tk.END, output)
            except json.decoder.JSONDecodeError:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    output = str(response.status_code) + "\n" + soup.prettify()
                    self.textBox.insert(tk.END, output)
        except requests.exceptions.InvalidURL as e:
            self.textBox.insert(tk.END, e)
        except requests.exceptions.ConnectionError as e:
            self.textBox.insert(tk.END, e)
        except requests.exceptions.ReadTimeout as e:
            self.textBox.insert(tk.END, e)


    def add_param(self):
        
        self.param_values.append(tk.StringVar())
        self.param_keys.append(tk.StringVar())
        param_row = 3
        if self.param_keys.__len__()<=1:
            tk.CTkLabel(self.frm, text="parameters:",).grid(column=2,row=param_row-2)
            tk.CTkLabel(self.frm, text="key:",).grid(column=2,row=param_row-1)
            tk.CTkLabel(self.frm, text="value:",).grid(column=3,row=param_row-1)
        
        #add key
        self.param_key_fields.append(tk.CTkEntry(self.frm,textvariable=self.param_keys[self.param_key_fields.__len__()]))
        self.param_key_fields[self.param_key_fields.__len__()-1].grid(column=2,row=param_row+self.param_key_fields.__len__()-1)
        
        #add value
        self.param_value_fields.append(tk.CTkEntry(self.frm,textvariable=self.param_values[self.param_value_fields.__len__()]))
        self.param_value_fields[self.param_value_fields.__len__()-1].grid(column=3,row=param_row+self.param_value_fields.__len__()-1)
        

    def add_data(self):
        
        self.data_values.append(tk.StringVar())
        self.data_keys.append(tk.StringVar())
        data_row = 3
        if self.data_values.__len__()<=1:
            tk.CTkLabel(self.frm, text="Data fields:",).grid(column=4,row=data_row-2, pady = 5, padx = 5)
            tk.CTkLabel(self.frm, text="key:",).grid(column=4,row=data_row-1, pady = 5, padx = 5)
            tk.CTkLabel(self.frm, text="value:",).grid(column=5,row=data_row-1, pady = 5, padx = 5)
        
        #add key
        self.data_key_fields.append(tk.CTkEntry(self.frm,textvariable=self.data_keys[self.data_key_fields.__len__()]))
        self.data_key_fields[self.data_key_fields.__len__()-1].grid(column=4,row=data_row+self.data_key_fields.__len__()-1)
        
        #add value
        self.data_value_fields.append(tk.CTkEntry(self.frm,textvariable=self.data_values[self.data_value_fields.__len__()]))
        self.data_value_fields[self.data_value_fields.__len__()-1].grid(column=5,row=data_row+self.data_value_fields.__len__()-1)

    
    def post_request(self):
        self.getCtrlinfo("post")
    
    def get_request(self):
        self.getCtrlinfo("get")

    def put_request(self):
        self.getCtrlinfo("put")
    
    def delete_request(self):
        self.getCtrlinfo("delete")

    #Websocket callbacks
    def on_message(self, ws, message):
        soup = BeautifulSoup(message, 'html.parser')
        self.subTextBox.insert(tk.END, soup.prettify()+ "\n\n")
        
        
    def on_error(self, ws, error):
        self.subTextBox.insert(tk.END, error)

    def on_close(self, ws, close_status_code, close_msg):
        self.subTextBox.insert(tk.END,"### closed ### \n")

    def on_open(self, ws):
        self.subTextBox.insert(tk.END,"Opened connection\n")

    #init websocket    
    def uppgrate_socket(self):
        if self.switch_var.get() == "RWS 1.0":
            subProt = 'robapi2_subscription'
        elif self.switch_var.get() == "RWS 2.0":
            subProt = 'rws_subscription'
        try:
            self.wsObject = RWSSocket(self.httpReqObj.cookie_string,self.text.get(),subProt)
            self.wsObject.ws.on_open = self.on_open
            self.wsObject.ws.on_message = self.on_message
            self.wsObject.ws.on_error = self.on_error
            self.wsObject.ws.on_close = self.on_close
            self.thread = threading.Thread(target=self.wsObject.connectThr) 
            self.thread.start()
        except AttributeError as e:
                 self.textBox.insert(tk.END,  "no session initiated yet\n")   
        

    
    def kill_socket(self):
        self.wsObject.killSock()
        #self.thread.join()  

    def delete_data(self):
        if self.data_key_fields.__len__() >1:
            self.data_key_fields[self.data_key_fields.__len__()-1].destroy()
            self.data_value_fields[self.data_value_fields.__len__()-1].destroy()
            self.data_values.pop()
            self.data_keys.pop()
            self.data_key_fields.pop()
            self.data_value_fields.pop()

    def delete_param(self):
        if self.param_key_fields.__len__() >1:
            self.param_key_fields[self.param_key_fields.__len__()-1].destroy()
            self.param_value_fields[self.param_value_fields.__len__()-1].destroy()
            self.param_values.pop()
            self.param_keys.pop()
            self.param_key_fields.pop()
            self.param_value_fields.pop()

    def sessionReset(self):
        self.session=None

    def switch_event(self):
        self.v_switch.configure(text=self.switch_var.get())
    
    def switch_type_event(self):
        self.type_switch.configure(text=self.switch_type.get())
        

    def __init__(self):
        
        # Create the main window
        tk.set_appearance_mode("dark")
        tk.set_default_color_theme("green")
        self.root = tk.CTk()
        self.root.title("RWS Test Tool")
        self.root.geometry("1200x800")
        self.frm = tk.CTkFrame(self.root)
        self.frm.pack(pady = 10,padx = 10, side = "top")

        #self.outputText = tk.StringVar()
        self.textBox = tk.CTkTextbox(self.root,height = 400, width= 700)
        self.textBox.pack(pady = 10, padx = 10, side = "left", expand = True)

        self.subTextBox = tk.CTkTextbox(self.root,height = 400, width= 400, )
        self.subTextBox.pack(pady = 10, padx = 10, side = "right",expand = True)
        

        #collumn 0
        button_text_color = "black"
        button_padding = 3
        tk.CTkButton(self.frm, text="get", command=self.get_request, text_color=button_text_color).grid(column=0,row=1,padx = button_padding, pady = button_padding)
        
        tk.CTkButton(self.frm, text="post", command=self.post_request,text_color=button_text_color,).grid(column=0,row=2,padx = button_padding, pady = button_padding)

        tk.CTkButton(self.frm, text="put", command=self.put_request,text_color=button_text_color,).grid(column=0,row=3,padx = button_padding, pady = button_padding)

        tk.CTkButton(self.frm, text="delete", command=self.delete_request,text_color=button_text_color,).grid(column=0,row=4,padx = button_padding, pady = button_padding)

        tk.CTkButton(self.frm, text="start subscription", command=self.uppgrate_socket,text_color=button_text_color,).grid(column=0,row=5,padx = button_padding, pady = button_padding)
        
        tk.CTkButton(self.frm, text="add url parameter", command=self.add_param, text_color=button_text_color).grid(column=0,row=6, padx = button_padding, pady = button_padding)
        
        tk.CTkButton(self.frm, text="add data", command=self.add_data,text_color=button_text_color).grid(column=0,row=7,padx = button_padding, pady = button_padding)
    
        tk.CTkButton(self.frm, text="delete url parameter", command=self.delete_param,text_color=button_text_color).grid(column=0,row=8,padx = button_padding, pady = button_padding)

        tk.CTkButton(self.frm, text="delete data", command=self.delete_data,text_color=button_text_color).grid(column=0,row=9,padx = button_padding, pady = button_padding)

        tk.CTkButton(self.frm, text="new session", command=self.sessionReset,text_color=button_text_color).grid(column=0,row=10,padx = button_padding, pady = button_padding)

        tk.CTkButton(self.frm, text="end subscription", command=self.kill_socket,text_color=button_text_color).grid(column=0,row=11,padx = button_padding, pady = button_padding)
        
        

        #collumn 1
    
        self.text= tk.StringVar()
        tk.CTkLabel(self.frm, text="URI:").grid(column=1,row=2)
        
        self.textbox = tk.CTkEntry(self.frm,textvariable=self.text).grid(column=1,row=3)
        
        self.add_data()
        self.add_param()

        #version switch
        self.switch_var = tk.StringVar(value="RWS 1.0")
        self.v_switch = tk.CTkSwitch(self.frm,progress_color="transparent",variable=self.switch_var, onvalue="RWS 2.0", offvalue="RWS 1.0",
                                command=self.switch_event, text=self.switch_var.get())
        

        self.v_switch.grid(column = 10,row = 1)
       
        #return switch
        self.switch_type = tk.StringVar(value="json")
        self.type_switch = tk.CTkSwitch(self.frm,progress_color="transparent",variable=self.switch_type, onvalue="XML", offvalue="json",
                                command=self.switch_type_event, text=self.switch_type.get())
        

        self.type_switch.grid(column = 5,row = 1)

        #add IP
        self.ip_addr = tk.StringVar(value="localhost")
        tk.CTkLabel(self.frm, text="ip address").grid(column=10, row = 2)
        ip_field = tk.CTkEntry(self.frm, textvariable=self.ip_addr,width=100)
        ip_field.grid(column=10, row = 3)

        #add port
        self.port_number = tk.StringVar(value="80")
        tk.CTkLabel(self.frm, text="port number").grid(column=10, row = 4)
        port_field = tk.CTkEntry(self.frm, textvariable=self.port_number,width=50)
        port_field.grid(column=10, row = 5)

        


        # Start the main loop
        self.root.mainloop()

test = test_rws()