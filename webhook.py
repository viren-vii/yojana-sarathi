from datetime import datetime
from flask import Flask, jsonify, request, Response, redirect, url_for
import requests
from requests.structures import CaseInsensitiveDict
import json
import os
from adhaar import getAdhaarData
import urllib
from flask import Flask, render_template

from sqlalchemy import null, and_, or_
from models import Accounts, Schemes, Users, db, AppliedSchemes

now = datetime.now()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://<database_username>:<user_password>@localhost/<database_name>'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

STARTER_MESSAGE = """Welcome To Yojna Sarathi || योजना सारथी!\\nPlease enter language code:\\n1. English\\n2. Hindi\\nकृपया भाषा क्रमांक डाले:\\n1. इंग्रजी\\n2. हिंदी"""

MAIN_MENU = """Yojna Sarathi \\nMain Menu \\n\\nUsers:\\n!users > To list users\\n!user add > To add user\\n!user delete > To remove user\\n!user select <id> > To select specified user\\n\\nInformation Update:\\n!adhaar > Update Aadhaar \\n!category > Update category \\n!income > Update income \\n\\nSchemes:\\n!schemes > To get schemes for which user is eligible\\n!apply <id> > Apply to particular scheme\\n!status > Status of schemes for which user have applied"""
# कृपया भाषा क्रमांक डाले:
# १. इंग्रजी
# २. हिंदी
# योजना सारथी

CATEGORY_SELECTION = """Please select your category:\\n1 SC\\n2 ST\\n3 OBC\\n4 VJNT\\n5 PWD\\n6 Father ex-serviceman\\n7 Widow\\n8 Senior Citizen"""


CATEGORY_MAPPING = ['SC', 'ST', 'OBC', 'VJNT', 'PWD',
                    'Father ex-serviceman', 'Widow', 'Senior Citizen']

INCOME_INPUT = """Please enter your annual income"""


def send_message(message, recipient, message_code):
    url = "https://graph.facebook.com/v13.0/110115441801170/messages"
    headers = CaseInsensitiveDict()
    headers["Authorization"] = "Bearer <bearer_token>"
    headers["Content-Type"] = "application/json"
    data = f"""
        {{"messaging_product":"whatsapp","recipient_type":"individual",
        "to":"{recipient}","type":"text","text": {{"body":"{message}"}}
        }}
        """

    resp = requests.post(url, headers=headers, data=data.encode('utf-8'))
    print(resp.json())
    if resp.status_code == 200:
        user = getUser(recipient)
        print("Printing user ****************", user, message)
        user.last_message = message_code
        db.session.commit()
    return resp.status_code


@app.before_first_request
def create_table():
    print("Creating db")
    db.create_all()


@app.route('/')
def main():
    return "Yojna Sarathi"


@app.route('/webhooks', methods=['GET', 'POST'])
def return_response():
    if request.method == 'POST':
        data = json.loads(request.data)
        print(data)
        messagesObj = data['entry'][0]['changes'][0]['value']

        if 'messages' in messagesObj:
            messages = messagesObj['messages'][0]
            SENDER = messages["from"]
            LANG = getLangugage(SENDER)
            LAST_MESSAGE = getLastMessage(SENDER)
            CURRENT_ACCOUNT = getUser(SENDER)
            CURRENT_USER = None
            if CURRENT_ACCOUNT != None:
                CURRENT_USER = Users.query.filter_by(
                    id=CURRENT_ACCOUNT.curr_user).first()
            print(LANG)
            print(messages)
            if messages["type"] == 'text':
                body = messages["text"]["body"]
                print(body, "-----------------------------------------")
                # print(send_message('Wait till we process your message', SENDER))
                if LAST_MESSAGE == None:
                    createNewAccount(SENDER)
                    print("Sending Starter Message",
                          send_message(STARTER_MESSAGE, SENDER, 'SETLANG'))
                elif LAST_MESSAGE == 'SETLANG':
                    if '2' in body:
                        LANG = 'HIN'
                    elif '1' in body:
                        LANG = 'ENG'
                    user = getUser(SENDER)
                    user.lang = LANG
                    db.session.commit()
                    print("Setting language setted", send_message(
                        "Langugage set to " + LANG, SENDER, 'MENU'))
                    print("Sending Menu", send_message(
                        MAIN_MENU, SENDER, 'MENU'))
                elif "!menu" in body:
                    print("Sending Menu", send_message(
                        MAIN_MENU, SENDER, 'MENU'))
                elif "!user" in body:
                    handleUserCommand(SENDER, body)
                elif '!category' in body:
                    print("Category input", send_message(
                        CATEGORY_SELECTION, SENDER, 'CATEGORYIP'))
                elif '!income' in body:
                    print("Income Input", send_message(
                        INCOME_INPUT, SENDER, "INCOMEIP"))
                elif '!schemes' in body:
                    processSchemes(SENDER, False)
                elif '!status' in body:
                    showStatus(SENDER)
                elif '!apply' in body:
                    applyScheme(SENDER, body)
                elif LAST_MESSAGE == 'CATEGORYIP':
                    categories = body.split(' ')
                    categories = [int(c) for c in categories]
                    CURRENT_USER.user_category = categories
                    db.session.commit()
                    print("Send Category Confirmation", send_message(
                        "Category set successful.\\n", SENDER, "CATSET"))
                    if '!category' not in body:
                        print("Income Input", send_message(
                            INCOME_INPUT, SENDER, "INCOMEIP"))
                elif LAST_MESSAGE == 'INCOMEIP':
                    CURRENT_USER.user_income = int(body)
                    db.session.commit()
                    print("Send Income Confirmation", send_message(
                        "Income set successful.\\n", SENDER, "INCOMESET"))
                    if '!income' not in body:
                        print("Detail Input Complete", send_message(
                            "Information inputs are completed", SENDER, "INFOCOMPLETE"))
                else:
                    print("Sending Error Message",
                          send_message("Sorry, please send message again.", SENDER, LAST_MESSAGE))
                return "SENT MESSAGE"
            elif messages["type"] == 'image' and LAST_MESSAGE == "SENDADHAAR":
                MEDIA_ID = messages["image"]["id"]
                headers = CaseInsensitiveDict()
                headers["Authorization"] = "Bearer <bearer_token>"
                getUrl = 'https://graph.facebook.com/v14.0/' + MEDIA_ID
                resp = requests.get(getUrl, headers=headers)
                print("got image:", resp.json()['url'])

                downloadUrl = resp.json()['url']
                r = requests.get(downloadUrl, headers=headers)

                content_type = r.headers['Content-Type']
                username = SENDER
                CURR_USER = getUser(SENDER).users_count
                if content_type == 'image/jpeg':
                    filename = f'uploads/{username}/{CURR_USER}.jpg'
                elif content_type == 'image/png':
                    filename = f'uploads/{username}/{CURR_USER}.png'
                elif content_type == 'image/gif':
                    filename = f'uploads/{username}/{CURR_USER}.gif'
                else:
                    filename = None
                if filename:
                    if not os.path.exists(f'uploads/{username}'):
                        os.mkdir(f'uploads/{username}')
                    with open(filename, 'wb') as f:
                        f.write(r.content)
                    print("IMGRECV", send_message(
                        'Thank you! Your image was received.', SENDER, 'IMGRECV'))
                    account = getUser(SENDER)
                    account.users_count = account.users_count + 1
                    userData = getAdhaarData(
                        f'uploads/{username}/{CURR_USER}.jpg')
                    if userData == None:
                        print("Send Adhaar", send_message(
                            "Please send clear Adhaar card photo again", SENDER, "SENDADHAAR"))
                        return "POST failed recieved photo"
                    new_user = Users(
                        user_name=userData['name'], user_age=userData['age'], user_gender=userData['gender'], user_pincode=userData['pincode'], user_state=userData['state'], account_id=account.account_id)
                    db.session.add(new_user)
                    db.session.commit()
                    account.curr_user = new_user.id
                    db.session.commit()
                    print("$$$$$$$$$$$$$$$$$$$", account.curr_user)
                    print("$$$$$$$$$$$$$$$$$$$", account.curr_user)
                    print("IMGCONFIRM", send_message("User registered succesfully!\\n",
                                                     SENDER, 'IMGCONFIRM'))
                    print("Category input", send_message(
                        CATEGORY_SELECTION, SENDER, 'CATEGORYIP'))
                    return "POST recieved photo"
                else:
                    send_message(
                        'The file that you submitted is not a supported image type.', SENDER, 'IMGERR')
                    return "POST failed recieved photo"

        return "POST"
    else:
        local_verify_token = "vtoken1029384756"
        print(request)
        args = request.args
        print(args.get("hub.mode"))
        print(args.get("hub.challenge"))
        print(args.get("hub.verify_token"))
        if args.get("hub.verify_token") != local_verify_token:
            return "Invalid verify token", 400
        return args.get("hub.challenge")


@app.route('/data')
def RetrieveDataList():
    accounts = Accounts.query.all()
    users = Users.query.all()

    newaccount = Accounts('001234567890')
    db.session.add(newaccount)
    db.session.commit()

    print(accounts)
    print(users)
    return "Data"


@app.route('/test')
def test():
    return str(isNewAccount('919423587762'))


@app.route('/applied_schemes/', methods=["GET", "POST"])
def applied_schemes_route():
    if request.method == 'POST':
        print(request.form)
        for key in request.form:
            if 'open' in key or 'close' in key:
                scheme_id = key.split('+')[1]
                status = key.split('+')[2]

        print("__________________", scheme_id, status)

        scheme = AppliedSchemes.query.filter_by(id=scheme_id).first()
        scheme_code = Schemes.query.filter_by(
            scheme_id=scheme.scheme_id).first().scheme_code
        user_id = scheme.user_id
        account = Users.query.filter_by(id=user_id).first().account_id
        account = Accounts.query.filter_by(account_id=account).first()
        account_number = account.account_number
        if status == 'A':
            print("Seding acceptance", send_message("Your application for " +
                  scheme_code+" is approved!", account_number, 'APPROVED'))
        elif status == 'R':
            print("Seding rejection", send_message("Your application for " +
                  scheme_code+" is rejected!", account_number, 'REJECTED'))

        scheme.status = status
        db.session.commit()

        return redirect('/applied_schemes')
    elif request.method == 'GET':
        applied_schemes = AppliedSchemes.query.all()
        data = []

        for scheme in applied_schemes:
            user = Users.query.filter_by(id=scheme.user_id).first()
            name = user.user_name
            age = user.user_age
            gender = user.user_gender
            category = ""
            for c in user.user_category:
                category += str(c) + " "
            income = user.user_income
            applied_scheme = Schemes.query.filter_by(
                scheme_id=scheme.scheme_id).first().scheme_code
            applied_scheme_id = scheme.id
            applied_scheme_status = 'Pending'
            if scheme.status == 'A':
                applied_scheme_status = 'Approved'
            elif scheme.status == 'R':
                applied_scheme_status = 'Rejected'
            row = {
                'name': name,
                'applied_scheme': applied_scheme,
                'age': age,
                'gender': gender,
                'category': category,
                'income': income,
                'applied_scheme_id': applied_scheme_id,
                'applied_scheme_status': applied_scheme_status
            }
            data.append(row)
        return render_template('applied_schemes.html', data=data)


def changeStatus(applied_scheme_id, setStatus):
    print('Button clicked', applied_scheme_id, setStatus)


def applyScheme(account_number, query):
    user = getUser(account_number).curr_user
    user = Users.query.filter_by(id=user).first()
    user_id = user.id
    print(user_id)
    schemes = processSchemes(account_number, True)
    print(schemes)
    scheme_id = schemes[int(query.split(' ')[1])-1].scheme_id
    print(scheme_id)
    applied_scheme = AppliedSchemes(scheme_id, user_id)
    db.session.add(applied_scheme)
    db.session.commit()
    print("Applied for scheme", send_message(
        "Applied for scheme succesfully", account_number, "APPLIEDSCHEME"))
    return


def handleUserCommand(account_number, query):
    account = getUser(account_number)
    account_id = account.account_id
    all_users = Users.query.filter_by(account_id=account_id).all()
    print(all_users)
    print(query)
    users_message = "Users in your list are:\\n"
    i = 0
    for user in all_users:
        i += 1
        users_message += str(i) + " " + user.user_name+"\\n"
    if '!users' in query:
        send_message(users_message, account_number, 'USERLIST')
    elif '!user select' in query:
        index = int([dig for dig in query if dig.isdigit()][0]) - 1
        selected_user_id = all_users[index].id
        selected_user = all_users[index]
        account.curr_user = selected_user_id
        categories_code = selected_user.user_category
        categories = ""
        for c in categories_code:
            categories += CATEGORY_MAPPING[c-1] + " "
        userInfo = f"""\\nName: {selected_user.user_name}\\nAge: {selected_user.user_age}\\nGender: {selected_user.user_gender}\\nIncome: {selected_user.user_income}\\nCategories: {categories}"""
        send_message("Selected user: " + userInfo,
                     account_number, 'SELECTEDUSER')
    elif '!user add' in query:
        print("Send Adhaar", send_message(
            "Please send Adhaar card photo", account_number, "SENDADHAAR"))
    return


def createNewAccount(account_number):
    account = Accounts(account_number)
    db.session.add(account)
    db.session.commit()


def showStatus(account_number):
    user = getUser(account_number).curr_user
    user = Users.query.filter_by(id=user).first()
    print(user.id)
    appliedSchemes = AppliedSchemes.query.filter_by(user_id=user.id).all()
    print("Applied Schemes: ", appliedSchemes)
    status_message = ""
    i = 0
    # print(appliedSchemes)
    if len(appliedSchemes) == 0:
        print("Sending status not available", send_message(
            "You have not applied to any of the scheme", account_number, 'NOSTATUS'))
    for scheme in appliedSchemes:
        i += 1
        status_message += f"{i}\\n"
        schemeData = Schemes.query.filter_by(
            scheme_id=scheme.scheme_id).first()
        # print(schemeData)
        status_message += f"Scheme: \\n{schemeData}\\n"
        status_message += f"Applied on: {scheme.applied_date}\\n"
        status = 'Pending'
        if scheme.status == 'R':
            status = 'Rejected'
        elif scheme.status == 'A':
            status = 'Accepted'

        status_message += f"Status: {status}\\n"

    print("Sending Status", send_message(
        status_message, account_number, "SENTSTATUS"))
    return


def isNewAccount(account_number):
    allAccounts = Accounts.query.all()
    print(allAccounts)
    for acc in allAccounts:
        if acc.account_number == account_number:
            return False
    return True


def processSchemes(account_number, applyScheme):
    user = getUser(account_number).curr_user
    user = Users.query.filter_by(id=user).first()
    print(user)
    # byGender = Schemes.query.filter_by(eligible_gender=user.user_gender).all()
    # byAge = Schemes.query.filter_by(
    #     and_(user.user_age >= Schemes.min_age, user.user_age <= Schemes.max_age)).all()
    # byAge = db.session.query(Schemes).filter(
    #     and_(user.user_age >= Schemes.min_age, user.user_age <= Schemes.max_age)).all()
    # categoryBool = False
    # if any(ele in user.user_category for ele in Schemes.eligible_category):
    #     categoryBool = True

    # print(byGender)
    print("------------------------------------------")
    print(Schemes.eligible_income)
    # print(byAge)
    schemes = db.session.query(Schemes).filter(and_(user.user_age >= Schemes.min_age,
                                                    user.user_age <= Schemes.max_age, user.user_gender == Schemes.eligible_gender, ((Schemes.eligible_income == None) | (Schemes.eligible_income >= user.user_income)))).all()
    scheme_message = ""
    # schemes = byGender
    print(type(schemes))
    if applyScheme:
        return schemes
    i = 0
    for scheme in schemes:
        i += 1
        scheme_message += f"{i}\\n"
        if scheme.scheme_code != null:
            scheme_message += f"*Scheme code:* {scheme.scheme_code}\\n"
        if scheme.description != null:
            scheme_message += f"*Scheme description:* {scheme.description}\\n"
        if scheme.required_documents != null:
            docs = [doc for doc in scheme.required_documents]
            docs_string = '\\n'.join(docs)
            scheme_message += f"*Required documents for scheme:* \\n{docs_string}\\n"
        if scheme.link != null:
            scheme_message += f"*Links:* \\n"
            for l in scheme.link:
                scheme_message += f"{l}\\n"
        scheme_message += "\\n\\n"
    print("Scheme message: ", scheme_message)
    if len(scheme_message) > 0:
        send_message(scheme_message, account_number, "SCHEMESENT")
    else:
        send_message("No scheme available for you",
                     account_number, "SCHEMESENT")
    return


def getUser(account_number):
    return Accounts.query.filter_by(account_number=account_number).first()


def getLangugage(account_number):
    user = Accounts.query.filter_by(account_number=account_number).first()
    if user != None:
        return user.lang
    return None


def getLastMessage(account_number):
    user = Accounts.query.filter_by(account_number=account_number).first()
    if user != None:
        return user.last_message
    return None


if __name__ == "__main__":
    app.run()
"""

request.data

b'{
    "object":"whatsapp_business_account",
    "entry":[
        {
            "id":"105422282277889",
            "changes":[
                {
                    "value":{
                        "messaging_product":"whatsapp",
                        "metadata":{
                            "display_phone_number":"15550018246",
                            "phone_number_id":"110115441801170"},
                            "contacts":[
                                {
                                    "profile":{
                                        "name":"Viren Bhosale"
                                    },
                                    "wa_id":"919423587762"
                                }
                            ],
                        "messages":[
                            {
                                "from":"919423587762",
                                "id":"wamid.HBgMOTE5NDIzNTg3NzYyFQIAEhggMDk2NzdEMzYzRkRCQThDOUFDRDlFODY3MjFGNUJGMDQA",
                                "timestamp":"1660820731",
                                "text":{
                                    "body":"Sunne message"
                                },
                                "type":"text"
                            }
                        ]
                    },
                    "field":"messages"
                }
            ]
        }
    ]
}'





curl -X  POST \
 'https://graph.facebook.com/v14.0/110115441801170/messages' \
 -H 'Authorization: Bearer EAAuYFP2FD7oBAAWbzcI8E1CB0qUvwn0itZCa99hbl4oFFnTY0ZAtfOKp44eOcy49jLXibkqRciX2EEhVzuhdwy3rfm1jHJ0g92KNMBZBEgoDWCsus9CsLASt6XjzgqCzZCDZBpJT0xKxrd63L2MuXS3XtdNJZBXgI1VWcLzmL1kYXzhhjkn9DQ4ZCJbTdQT9gqNMFcJbUK7wwZDZD' \
 -d '{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "919423587762",
  "type": "text",
  "text": { // the text object
    "preview_url": false,
    "body": "MESSAGE_CONTENT"
  }
}'


curl --location --request POST 'https://graph.facebook.com/v13.0/110115441801170/messages' \
--header 'Authorization: Bearer EAAuYFP2FD7oBAAWbzcI8E1CB0qUvwn0itZCa99hbl4oFFnTY0ZAtfOKp44eOcy49jLXibkqRciX2EEhVzuhdwy3rfm1jHJ0g92KNMBZBEgoDWCsus9CsLASt6XjzgqCzZCDZBpJT0xKxrd63L2MuXS3XtdNJZBXgI1VWcLzmL1kYXzhhjkn9DQ4ZCJbTdQT9gqNMFcJbUK7wwZDZD' \
--header 'Content-Type: application/json' \
--data-raw '{"messaging_product":"whatsapp","recipient_type":"individual",
"to":"919423587762","type":"text","text": {"body":"Hello World!"}
}'

"""
