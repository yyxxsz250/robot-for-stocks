#!/usr/bin/env python
# coding: utf-8

# In[1]:


#get imformation from iefinance
from iexfinance import get_available_symbols
from iexfinance import Stock
iu=get_available_symbols(output_format='dict')
from iexfinance import get_market_tops
from iexfinance import get_stats_intraday
shizhi=get_market_tops()

#make the robot learn to interpret
import spacy
nlp=spacy.load("en_core_web_md")
from rasa_nlu.training_data import load_data
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer
from rasa_nlu import config
trainer = Trainer(config.load("config_spacy.yml"))
data=load_data('studing.json')
interpreter = trainer.train(data)

#get necessary tools
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re


# In[19]:





# In[10]:





# In[49]:


#Creat a function to wipe some useless letters in a stock's name.
gongsihouzhui=re.compile(r" (inc|corporation|company|fund)")
def quhouzhui(name):
    nam=str.lower(name)
    x=re.search(gongsihouzhui,nam)
    if x is not None:
        nam=re.sub(gongsihouzhui,'',nam)
    return nam

#creat a function to compare the word with the stocks' names.
def pipei_name(name):
    Fa=0
    nam=None
    for gupiao in iu:
        if fuzz.ratio(str.lower(name), str.lower(gupiao['name']))>=90:
            return gupiao['symbol'],0
        if fuzz.ratio(name, gupiao['symbol'])==100:
            return gupiao['symbol'],0
        if fuzz.ratio(str.upper(name), gupiao['symbol'])==100:
            return gupiao['symbol'],1
        if (fuzz.ratio(quhouzhui(name), quhouzhui(gupiao['name']))>=70)&(fuzz.ratio(quhouzhui(name), quhouzhui(gupiao['name']))>Fa):
            #print(fuzz.ratio(quhouzhui(name), quhouzhui(gupiao['name'])))
            Fa=fuzz.ratio(quhouzhui(name), quhouzhui(gupiao['name']))
            nam=gupiao['symbol']
                      #return gupiao['name']       
    return nam,1

#creat a function to get a name from the message
def find_name(message):
    a,b=pipei_name(message)
    if a!=None:
        return a,b
    doc=nlp(message)
    for token in doc:
        #print(token.tag_)
        if (token.tag_=='.')|(token.tag_=='NNP')|(token.tag_=='NN')|((str(token)==(str.upper(str(token))))&(token.pos_!="PRON")):
            a,b=pipei_name(str(token))
            if a!=None:
                return a,b
    return None,1
#        DOC=nlp(token)
#        for TOKEN in DOC:
#            print(TOKEN.tag_)

a,b=find_name( 'I')
print(a,b)

#creat a function to learn what information about the stock the user want to know.
def find_info(message):
    info=[]
    if re.search(re.compile(r"(volume|bidsize)"),message):
        info.append('lastSaleSize')
    if re.search(re.compile(r"(price|value|rate)"),message):
        info.append('lastSalePrice')
    if re.search(re.compile(r"(share|percent)"),message):
        info.append('marketPercent')
    return info


# In[4]:


#define three states in conversation
INIT=0
COMFIRM_NAME=1
ASKING_INFO=2

#define some dicts to use for creating response
policy = {
    (INIT,"greet"): (INIT, "Hello!How can I help you?"),
    (INIT,"chatting"): (INIT, "oh, that's so funny.Would you ask me something about the market?"),    
    (INIT,"affirm"): (INIT, "what are you affirm for?Why don't you ask me the price of it's stock?"),
    (INIT,"deny"): (INIT, "what are you deny for?Why don't you ask me the price of it's stock?"),
    (COMFIRM_NAME,"chatting"):(COMFIRM_NAME,"I'm so pressure to hear that from you, but you haven't answer me yet! Did I got your heart?"),
    (COMFIRM_NAME,"greet"):(COMFIRM_NAME,"you're welcome. Anyway, am i right?"),
    (COMFIRM_NAME,"asking"):(COMFIRM_NAME,"tell me if i'm right first!Or i will come into chaos "),
    (ASKING_INFO,"deny"):(INIT,"'m so sorry to here that. Maybe we can start all over again."),
#    (ASKING_INFO,"deny"):(INIT,"I'm so sorry to here that. Maybe we can start all over again.")，
    (ASKING_INFO,"chatting"):(ASKING_INFO,"oh, that's so funny. So would yoou like to continue our searching on that stock? I was just enjoying our conversation"),
     (ASKING_INFO,"greet"): (ASKING_INFO, "Hello!How can I help you?"),
}

response_infos=[
    "sorry, I can't find infomations you need on internet now, what an unlucky matter",
    "The {1} of {0} is {2}.",
    "The {1} of {0} is {2},and the {3} is {4}.",
    "The {1} of {0} is {2}, the {5} is {6} and the {3} is {4}."
]


# In[ ]:





# In[21]:


#main function to response
def respond(policy,state, name, message):
    intent = interpreter.parse(message)['intent']['name']
    if state ==INIT:
        if  (intent=="asking")|(intent=="affirm"):
            nam,x=find_name(message)
            if nam!=None:
                name=nam
                if x==1:
                    response="are you talking about {}?".format(name)
                    return COMFIRM_NAME,name,response
                info=find_info(message)
                if len(info)==0:
                    response="which data do you want to know about {}?".format(name)
                    return ASKING_INFO,name,response
                lisy=[]
                lisy.append(name)
                shizhi=get_market_tops()
                for gupiao in shizhi:
                    if gupiao['symbol']==name:
                        for item in info:
                            lisy.append(item)
                            lisy.append(gupiao[item])
                        break
                n=int((len(lisy)-1)/2)
                response=response_infos[n].format(*lisy)
                return INIT, None, response
            response="Sorry, can you tell me which stock do you want to inquire first？"
            return INIT, None, response
        new_state,response=policy[state,intent]
        return new_state, None ,response
    if state ==COMFIRM_NAME:
        if intent=="affirm":
            info=find_info(message)
            if len(info)==0:
                response="which data do you want to know about {}?".format(name)
                return ASKING_INFO,name,response
            lisy=[]
            lisy.append(name)
            shizhi=get_market_tops()
            for gupiao in shizhi:
                if gupiao['symbol']==name:
                    for item in info:
                        lisy.append(item)
                        lisy.append(gupiao[item])
                    break
            n=int((len(lisy)-1)/2)
            response=response_infos[n].format(*lisy)
            return INIT, None, response
        if intent=="deny":
            nam,x=find_name(message)
            if nam!=None:
                name=nam
                if x==1:
                    if nam==name:
                        response="sorry, I still just read out {}, can you say it again?Just the name of the stock, not other words, which would rise my acurrancy".format(name)
                        return INIT, name, response
                    response="So are you talking about {}?".format(name)
                    return COMFIRM_NAME,name,response
                info=find_info(message)
                if len(info)==0:
                    response="which data do you want to know about {}?".format(name)
                    return ASKING_INFO,name,response
                lisy=[]
                lisy.append(name)
                shizhi=get_market_tops()
                for gupiao in shizhi:
                    if gupiao['symbol']==name:
                        for item in info:
                            lisy.append(item)
                            lisy.append(gupiao[item])
                        break
                n=int((len(lisy)-1)/2)
                response=response_infos[n].format(*lisy)
                return INIT, None, response
            response="Sorry to misunderstand your words, can you tell me which stock do you want to inquire again？Just the name of the stock and do not say other words may rise my acurrancy"
            return INIT, None, response
        new_state,response=policy[state,intent]
        return new_state, name ,response
    if state==ASKING_INFO:
        if (intent=="asking")|(intent=="affirm"):
            info=find_info(message)
            if len(info)==0:
                response="I still fail to find out which data you wanted to know about {}, can you tell it clearlier?the price, bidsize or market share?".format(name)
                return ASKING_INFO,name,response
            shizhi=get_market_tops()
            lisy=[]
            lisy.append(name)
            for gupiao in shizhi:
                if gupiao['symbol']==name:
                    for item in info:
                        lisy.append(item)
                        lisy.append(gupiao[item])
                    break
            n=int((len(lisy)-1)/2)
            response=response_infos[n].format(*lisy)
            return INIT, None, response
        if intent=="deny":
            nam,x=find_name(message)
            if nam!=None:
                if x==1:
                    if nam==name:
                        response="sorry, I still just read out {}, can you say it again?Just the name of the stock, not other words, which would rise my acurrancy".format(name)
                        return INIT, name, response
                    response="So are you talking about {}?".format(name)
                    return COMFIRM_NAME,name,response
                name=nam
                info=find_info(message)
                if len(info)==0:
                    response="which data do you want to know about {}?".format(name)
                    return ASKING_INFO,name,response
                lisy=[]
                lisy.append(name)
                shizhi=get_market_tops()
                for gupiao in shizhi:
                    if gupiao['symbol']==name:
                        for item in info:
                            lisy.append(item)
                            lisy.append(gupiao[item])
                        break
                n=int((len(lisy)-1)/2)
                response=response_infos[n].format(*lisy)+"would you like to search other infomations about {}?".format(name)
                return ASKING_INFO, name, response
            response="good bye"
            return INIT, None, response
        new_state,response=policy[state,intent]
        return new_state, name ,response
            
                            
                


# In[22]:


#test the program
def send_message(policy,state,infos, message):
    print("USER : {}".format(message))
    new_state, new_infos, response = respond(policy,state,infos, message)
    print("BOT : {}".format(response))
    return new_state,new_infos,response
messages={
    "tesilaaaa",
    "yes,i want to know the values of it",
    "thank you",
    "i want to know price of TSLA today "
}
def shiyan(policy,messages):
    INIT=0
    COMFIRM_NAME=1
    ASKING_INFO=2
    state=INIT
    name=None
    for message in messages:
        #print (message)
        new_state, new_name,response=send_message(policy,state,name, message)
        name=new_name
        state=new_state
    return 0
shiyan(policy,messages)


# In[ ]:





# In[40]:


#Connect the robot to Weixin
from wxpy import *
bot=Bot()


# In[43]:


user = bot.friends().search('天')[0]
print(user)


# In[11]:





# In[50]:


INIT=0
COMFIRM_NAME=1
ASKING_INFO=2
state=INIT
name=None
@bot.register(user)
def reply_my_friend(msg):
    global state
    global name
    new_state, new_infos, response = send_message(policy,state,name,msg.text)
    state=new_state
    name=new_infos
    return response


# In[46]:





# In[134]:





# In[168]:





# In[ ]:




